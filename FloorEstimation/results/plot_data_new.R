library(ggplot2)
library(reshape2)
library(dplyr)

base_breaks_x <- function(x){
    b <- x
    d <- data.frame(y=-Inf, yend=-Inf, x=min(b), xend=max(b))
    list(geom_segment(data=d, size=1.3, colour="gray35", aes(x=x, y=y, xend=xend, yend=yend), inherit.aes=FALSE),
         scale_x_continuous(breaks=b))
}

base_breaks_x_discrete<- function(x, my.xend=5, scaled.scale=F){
    b <- x
    d <- data.frame(y=-Inf, yend=-Inf, x=1, xend=my.xend)
    if (scaled.scale) {
        scale = scale_x_discrete(limits=b)
    } else {
        scale = scale_x_discrete(limits=as.factor(b))
        }
        list(geom_segment(data=d, size=1.3, colour="gray35", aes(x=x, y=y, xend=xend, yend=yend), inherit.aes=FALSE), scale)
}

base_breaks_y <- function(x){
  b <- x
  d <- data.frame(x=-Inf, xend=-Inf, y=min(b), yend=max(b))
  list(geom_segment(data=d, size=1.3, colour="gray35", aes(x=x, y=y, xend=xend, yend=yend), inherit.aes=FALSE),
       scale_y_continuous(breaks=b))
}


#' Create a box-plot
plot.x.by.y <- function(df, x, y, xlab, ylab, out.name, report.dir,
                        plot.expected.error=FALSE, start.x.at=0,
                        plot.smooth=FALSE, extreme.outlier.count=NA,
                        count.outliers=F,
                        custom.base.breaks.x=c(0, 1, 2, 3, 4),
                        custom.base.breaks.y=seq(0, 25, 5),
                        my.fill="SETUP") {


	df[,x] <- as.factor(df[,x])
	df$NROB <- as.factor(df$NROB)
##    df <- df[df$byz >= start.x.at, ]
    

    #print(df)
    p <- ggplot(df, aes_string(x=x, y=y)) +
        geom_boxplot(width=0.8, aes_string(fill=my.fill)) +
        theme_classic() +
         theme(axis.text=element_text(size=15, colour="gray25"),
              axis.title=element_text(size=20, colour="gray25"),
              axis.line = element_blank(),              
              axis.ticks.length=unit(-0.25, "cm"),
              axis.ticks = element_line(colour = 'gray25'),
              panel.spacing.x=unit(.8, "lines"),
              #legend.position="none",
              strip.background = element_rect(size = 1.3),
              axis.text.x = element_text(margin=unit(c(0.3,0.3,0.3,0.3), "cm"),
                                         angle = 0, vjust = 0, hjust=0.5),
              axis.text.y = element_text(margin=unit(c(0.5,0.5,0.5,0.5), "cm")))  +
        ylab(ylab) +
        xlab(xlab) +
     base_breaks_y(custom.base.breaks.y) +
    base_breaks_x_discrete(custom.base.breaks.x, length(custom.base.breaks.x), FALSE)

    out.name <- file.path(report.dir, out.name)
    print(out.name)
    ggsave(out.name, width=7, height=4)    
}

#' Create blockchain size
plot.line <- function(df, x, y, xlab, ylab, out.name, report.dir,
                        plot.expected.error=FALSE, start.x.at=0,
                        plot.smooth=FALSE, extreme.outlier.count=NA,
                        count.outliers=F,
                        custom.base.breaks.x=c(0, 1, 2, 3, 4),
                        custom.base.breaks.y=seq(0, 25, 5)) {


    p <- ggplot(df, aes_string(x=x, y=y, color="NROB")) +
        geom_line() +
        theme_classic() +
         theme(axis.text=element_text(size=15, colour="gray25"),
              axis.title=element_text(size=20, colour="gray25"),
              axis.line = element_blank(),              
              axis.ticks.length=unit(-0.25, "cm"),
              axis.ticks = element_line(colour = 'gray25'),
              panel.spacing.x=unit(.8, "lines"),
              #legend.position="none",
              strip.background = element_rect(size = 1.3),
              axis.text.x = element_text(margin=unit(c(0.3,0.3,0.3,0.3), "cm"),
                                         angle = 0, vjust = 0, hjust=0.5),
              axis.text.y = element_text(margin=unit(c(0.5,0.5,0.5,0.5), "cm")))  +
        ylab(ylab) +
        xlab(xlab) +
     base_breaks_y(custom.base.breaks.y) +
    base_breaks_x(custom.base.breaks.x)

    out.name <- file.path(report.dir, out.name)
    print(out.name)
    ggsave(out.name, width=7, height=4)    
}


# Experiment 2
library(dplyr)

ground_truth = 0.25
experiments <- c("G1", "G2", "G3", "G4")
my_files = paste0("processed_data/csv_aggregated/combined_", experiments, ".csv")
my_data <- lapply(my_files, read.csv, sep=" ")
names(my_data) <- experiments

df <- bind_rows(my_data, .id = "EXP")
df$MEAN <- df$MEAN / 10000000
df$ERROR <- abs(df$MEAN - ground_truth)
df <- df[df$SETUP == "simulation",]

error_file = "error_2.png"
time_file = "time_2.png"

plot.x.by.y(df, "NBYZ", "ERROR", "Number of Byzantine robots", "Absolute error", error_file, ".",
    custom.base.breaks.x=c(0, 3, 6, 9, 12),
    custom.base.breaks.y=seq(0, 0.25, 0.05),
    my.fill="EXP")

plot.x.by.y(df, "NBYZ", "TIME", "Number of Byzantine robots", "Convergence time", time_file, ".",
    custom.base.breaks.x=c(0, 3, 6, 9, 12),
    custom.base.breaks.y=seq(0, 5000, 500),
    my.fill="EXP")


# Experiment 5, 6, and 9 (average connectivity)
library(dplyr)

experiments <- paste0("G", c(5, 6, 9))
my_files = paste0("processed_data/average_connectivity/peers_", experiments, ".csv")
my_data <- lapply(my_files, read.csv, sep=" ")
names(my_data) <- experiments
df <- bind_rows(my_data, .id = "EXP")

print(aggregate(df$CONNECTIVITY, by=list(EXP=df$EXP, NROB=df$NROB), FUN=mean))


#EXP = "G6"
#csv_file = paste0("processed_data/average_connectivity/peers_", EXP, ".csv")

#df <- read.csv(csv_file, sep=" ")
