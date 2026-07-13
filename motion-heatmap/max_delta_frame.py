"""
For each pixel in a video, find the frame where that pixel changed the most
(largest absolute difference vs. the previous frame), then build an image made
of each pixel's color value at that "peak motion" moment.

The video is split into contiguous chunks and decoded in parallel worker
processes (one process per CPU core by default), since each frame's delta only
depends on its immediate predecessor. Results are merged with an element-wise
max. Multiprocessing (not threading) is used because OpenCV's video decoding
is CPU-bound and doesn't benefit from Python threads.

Usage:
    python max_delta_frame.py "video.mp4" -o result.png --workers 8
"""

import argparse
import math
import multiprocessing as mp
import time

import cv2
import numpy as np


def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return fps, frame_count


def process_chunk(chunk_args):
    video_path, start_frame, end_frame, fps = chunk_args

    cap = cv2.VideoCapture(video_path)
    seek_to = max(start_frame - 1, 0)
    cap.set(cv2.CAP_PROP_POS_FRAMES, seek_to)
    ok, prev_frame = cap.read()
    if not ok:
        cap.release()
        return None

    h, w = prev_frame.shape[:2]
    best_delta = np.zeros((h, w), dtype=np.uint8)
    best_color = prev_frame.copy()
    best_time = np.zeros((h, w), dtype=np.float64)

    frame_idx = seek_to
    frames_read = 0
    while frame_idx + 1 < end_frame:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        frames_read += 1
        timestamp = frame_idx / fps if fps > 0 else float(frame_idx)

        diff = cv2.absdiff(frame, prev_frame)
        delta = diff.max(axis=2)

        mask = delta > best_delta
        if np.any(mask):
            best_delta[mask] = delta[mask]
            best_color[mask] = frame[mask]
            best_time[mask] = timestamp

        prev_frame = frame

    cap.release()
    return best_delta, best_color, best_time, frames_read


def merge_chunks(results):
    best_delta, best_color, best_time, _ = results[0]
    best_delta = best_delta.copy()
    best_color = best_color.copy()
    best_time = best_time.copy()

    for delta, color, timestamp, _ in results[1:]:
        mask = delta > best_delta
        best_delta[mask] = delta[mask]
        best_color[mask] = color[mask]
        best_time[mask] = timestamp[mask]

    return best_delta, best_color, best_time


def compute_max_delta_image(video_path, output_path, preview_path=None, workers=None):
    fps, frame_count = get_video_info(video_path)
    if frame_count <= 1:
        raise IOError("Video has too few frames")

    workers = workers or mp.cpu_count()
    workers = max(1, min(workers, frame_count - 1))

    chunk_size = math.ceil(frame_count / workers)
    chunks = [
        (video_path, start, min(start + chunk_size, frame_count), fps)
        for start in range(0, frame_count, chunk_size)
    ]

    print(f"Video has {frame_count} frames at {fps:.2f} fps. Using {workers} worker process(es).")
    t0 = time.time()

    if workers == 1:
        results = [process_chunk(chunks[0])]
    else:
        with mp.Pool(processes=workers) as pool:
            results = pool.map(process_chunk, chunks)

    results = [r for r in results if r is not None]
    if not results:
        raise IOError("No frames could be decoded")

    best_delta, best_color, best_time = merge_chunks(results)
    total_frames = sum(r[3] for r in results)

    elapsed = time.time() - t0
    print(f"Processed {total_frames} frames in {elapsed:.1f}s ({total_frames / elapsed:.1f} fps).")

    cv2.imwrite(output_path, best_color)
    print(f"Saved peak-delta image to: {output_path}")

    if preview_path:
        delta_vis = cv2.normalize(best_delta, None, 0, 255, cv2.NORM_MINMAX)
        cv2.imwrite(preview_path, delta_vis)
        print(f"Saved max-delta heatmap to: {preview_path}")

    print(
        f"Pixel timestamps range from {best_time.min():.3f}s to {best_time.max():.3f}s "
        f"(mean {best_time.mean():.3f}s)."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="Path to the input video")
    parser.add_argument(
        "-o", "--output", default="max_delta_image.png",
        help="Output image path (default: max_delta_image.png)"
    )
    parser.add_argument(
        "--preview", default=None,
        help="Optional path to save a grayscale heatmap of the max delta values"
    )
    parser.add_argument(
        "--workers", type=int, default=None,
        help="Number of parallel worker processes (default: number of CPU cores)"
    )
    args = parser.parse_args()

    compute_max_delta_image(args.video, args.output, args.preview, args.workers)
