suite1000<-function(r){
  un=0.99999
  list<-c(1:40)
  for(i in 1:40){
    un<-un*r*(1-un)
    list<-c(list[2:40],un)
  }
  return(list)
}

plot(1, type="n", xlab="Axe X", ylab="Axe Y", xlim=c(0.7,4),ylim=c(0,1.05))


for (i in seq(1,4.5,0.01)){
  yc<-suite1000(i)
  for(k in 1:40){
    points(i,yc[k],col=k,pch = 19,cex=0.01)
  }
}
