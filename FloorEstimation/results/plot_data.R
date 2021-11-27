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

my.theme <- theme(axis.text=element_text(size=15, colour="gray25"),
              axis.title=element_text(size=20, colour="gray25"),
              axis.line = element_blank(),              
              axis.ticks.length=unit(-0.25, "cm"),
              axis.ticks = element_line(colour = 'gray25'),
              panel.spacing.x=unit(.8, "lines"),
              legend.position="none",
              strip.background = element_rect(size = 1.3),
              axis.text.x = element_text(margin=unit(c(0.3,0.3,0.3,0.3), "cm"),
                                         angle = 0, vjust = 0, hjust=0.5),
              axis.text.y = element_text(margin=unit(c(0.5,0.5,0.5,0.5), "cm")))

#' Create a box-plot
plot.x.by.y <- function(df, x, y, xlab, ylab, out.name, report.dir,
                        plot.expected.error=FALSE, start.x.at=0,
                        plot.smooth=FALSE, extreme.outlier.count=NA,
                        count.outliers=F,
                        custom.base.breaks.x=c(0, 1, 2, 3, 4),
                        custom.base.breaks.y=seq(0, 25, 5),
                        annotation=NULL,
                        my.fill="SETUP") {


	df[,x] <- as.factor(df[,x])
	df$NROB <- as.factor(df$NROB)
    df$SETUP <- as.factor(df$SETUP)


    p <- ggplot(df, aes_string(x=x, y=y)) +
        geom_boxplot(width=0.8, aes_string(fill=my.fill)) +
        scale_fill_manual(values = c("#4daf4a", "#984ea3", "#e41a1c", "#377eb8")) +
        #geom_boxplot(data=df, aes(x=NBYZ, y=ESTIMATEERROR)) +
        annotation +
        theme_classic() +
         my.theme  +
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
         my.theme +
        ylab(ylab) +
        xlab(xlab) +
     base_breaks_y(custom.base.breaks.y) +
    base_breaks_x(custom.base.breaks.x)

    out.name <- file.path(report.dir, out.name)
    print(out.name)
    ggsave(out.name, width=7, height=4)    
}


ground_truth = 0.25

# Split df into results from simulation/reality and the average estimate
split.df <- function(df) {

    df$ESTIMATEERROR <- abs(df$AVGESTIMATE - ground_truth)
    df.estimate.error <- df[c("NROB", "NBYZ", "NREP", "ESTIMATEERROR")]
    names(df.estimate.error)[names(df.estimate.error) == 'ESTIMATEERROR'] <- 'ERROR'
    df.estimate.error$SETUP <- "baseline"

    df.experiments <- df[c("NROB", "NBYZ", "NREP", "ERROR", "SETUP")]

    df.full <- rbind(df.experiments, df.estimate.error)

    return(df.full)
}


# Experiment 1
EXP = "G1"
csv_file = paste0("processed_data/csv_aggregated/combined_", EXP, ".csv")
error_file = paste0("error_", EXP, ".png")
time_file = paste0("time_", EXP, ".png")

df <- read.csv(csv_file, sep=" ")
df$MEAN <- df$MEAN / 10000000
df$ERROR <- abs(df$MEAN - ground_truth)


df.full <- split.df(df)


my.annotation = annotate(geom = "text",
            x = c(0.72, 0.99, 1.25),
            y = 0.05,
            label = c("reality", "simulation", "baseline"),
            color = c("gray25"),
             angle = 90)

plot.x.by.y(df.full, "NBYZ", "ERROR", "Number of Byzantine robots", "Absolute error", error_file, ".",
    custom.base.breaks.x=c(0, 3, 6, 9, 12),
                        custom.base.breaks.y=seq(0, 0.25, 0.05),
                        annotation=my.annotation)

my.annotation = annotate(geom = "text",
            x = c(0.79, 1.18),
            y = 1600,
            label = c("reality", "simulation"),
            color = c("gray25"),
             angle = 90)

plot.x.by.y(df, "NBYZ", "TIME", "Number of Byzantine robots", "Convergence time", time_file, ".",
    custom.base.breaks.x=c(0, 3, 6, 9, 12),
                        custom.base.breaks.y=seq(0, 5000, 500),
                        annotation=my.annotation)


# Experiment 2
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


my.annotation = annotate(geom = "text",
            x = c(0.67, 0.88, 1.1, 1.28),
            y = 0.03,
            hjust = 0,
            label = c("always 0.0", "changing tile layout", "50:50", "uniform distribution"),
            color = c("gray25"),
             angle = 90)

plot.x.by.y(df, "NBYZ", "ERROR", "Number of Byzantine robots", "Absolute error", error_file, ".",
    custom.base.breaks.x=c(0, 3, 6, 9, 12),
    custom.base.breaks.y=seq(0, 0.25, 0.05),
    annotation=my.annotation,
    my.fill="EXP")

my.annotation = annotate(geom = "text",
            x = c(0.67, 0.88, 1.1, 1.28),
            y = 1300,
            hjust = 0,
            label = c("always 0.0", "changing tile layout", "50:50", "uniform distribution"),
            color = c("gray25"),
             angle = 90)

plot.x.by.y(df, "NBYZ", "TIME", "Number of Byzantine robots", "Convergence time", time_file, ".",
    custom.base.breaks.x=c(0, 3, 6, 9, 12),
    custom.base.breaks.y=seq(0, 5000, 500),
    annotation=my.annotation,
    my.fill="EXP")




EXPS = c("G5", "G6", "G9")

for (EXP in EXPS) {
    csv_file = paste0("processed_data/csv_aggregated/combined_", EXP, ".csv")
    error_file = paste0("error_", EXP, ".png")
    time_file = paste0("time_", EXP, ".png")

    df <- read.csv(csv_file, sep=" ")
    df$MEAN <- df$MEAN / 10000000
    df$ERROR <- abs(df$MEAN - ground_truth)

    df.full <- split.df(df)

    df.full.real <- df.full[df.full$SETUP == "reality",]
    df.full.sim <- df.full[df.full$SETUP == "simulation",]
    df.full.base <- df.full[df.full$SETUP == "baseline",]

    my.annotation = annotate(geom = "text",
                x = c(0.72, 0.99, 1.25),
                y = c(max(df.full.real$ERROR), max(df.full.sim$ERROR), max(df.full.base$ERROR)),
                hjust = 0,
                label = c("reality", "simulation", "baseline"),
                color = c("gray25"),
                 angle = 90)


    df.real <- df[df$SETUP == "reality",]
    df.sim <- df[df$SETUP == "simulation",]


    plot.x.by.y(df.full, "NROB", "ERROR", "Number of robots", "Absolute error", error_file, ".",
        custom.base.breaks.x=c(8, 16, 24),
                            custom.base.breaks.y=seq(0, 0.25, 0.05),
                            annotation=my.annotation)


    my.annotation = annotate(geom = "text",
                x = c(0.79, 1.18),
                y = c(max(df.real$TIME) + 200, max(df.sim$TIME) + 200),
                hjust = 0,          
                label = c("reality", "simulation"),
                color = c("gray25"),
                 angle = 90)

    plot.x.by.y(df, "NROB", "TIME", "Number of robots", "Convergence time", time_file, ".",
        custom.base.breaks.x=c(8, 16, 24),
                            custom.base.breaks.y=seq(0, 5000, 500),
                            annotation=my.annotation)

}


EXP = "G7"
csv_file = paste0("processed_data/csv_aggregated/combined_", EXP, ".csv")
estimate_file_8 = "/home/volker/final_data/data/Experiment_G7/8rob-0byz-1/216/sc.csv"
estimate_file_16 = "/home/volker/final_data/data/Experiment_G7/16rob-0byz-1/103/sc.csv"
estimate_file_24 = "/home/volker/final_data/data/Experiment_G7/24rob-0byz-1/103/sc.csv"
csv_file_8 = "/home/volker/final_data/data/Experiment_G7/8rob-0byz-1/216/extra.csv"
csv_file_16 = "/home/volker/final_data/data/Experiment_G7/16rob-0byz-1/103/extra.csv"
csv_file_24 = "/home/volker/final_data/data/Experiment_G7/24rob-0byz-1/103/extra.csv"
estimate_file = paste0("estimate_file", EXP, ".png")
blockchain_size_file = paste0("blockchain_size", EXP, ".png")


## Every x seconds (default: 512s), ancient chain data is moved to a
## backup folder; this disturbes the analysis of the folder size,
## therefore, remove this glitch
# See https://github.com/ethereum/go-ethereum/issues/15797 

remove.glitch <- function(df) {

    df$CHAINDATASIZE <- df$CHAINDATASIZE - df$CHAINDATASIZE[1] 
    pos.glitch <- which.max(diff(df$CHAINDATASIZE))
    diff.glitch <- max(diff(df$CHAINDATASIZE))
    copy.df <- df
    copy.df$CHAINDATASIZE <- df$CHAINDATASIZE - diff.glitch
    df.1 <- df[1:pos.glitch, ]
    glitch.plus.1 <- pos.glitch + 1
    df.2 <- copy.df[glitch.plus.1:nrow(copy.df), ]
    final.df <- rbind(df.1, df.2)

    return(final.df)
}

library(dplyr)

#NROBS <- c(8, 16, 24)
#extra.files <- c(csv_file_8, csv_file_16, csv_file_24)
#my_data <- lapply(extra.files, read.csv, sep=" ")
#df <- bind_rows(my_data, .id = "EXP")


df.8.estimate <- read.csv(estimate_file_8, sep=" ")
df.8.estimate$NROB = 8
df.16.estimate <- read.csv(estimate_file_16, sep=" ")
df.16.estimate$NROB = 16
df.24.estimate <- read.csv(estimate_file_24, sep=" ")
df.24.estimate$NROB = 24

df.estimate <- rbind(df.8.estimate, df.16.estimate, df.24.estimate)
df.estimate$MEAN <- df.estimate$MEAN / 10000000
df.estimate$NROB <- as.factor(df.estimate$NROB)
df.estimate <- df.estimate[df.estimate$MEAN != 0,]
df.estimate$TIME <- df.estimate$TIME
#print(df.estimate$TIME)

df.8 <- read.csv(csv_file_8, sep=" ")
df.8$NROB = 8
df.8 <- remove.glitch(df.8)
df.16 <- read.csv(csv_file_16, sep=" ")
df.16$NROB = 16
df.16 <- remove.glitch(df.16)
df.24 <- read.csv(csv_file_24, sep=" ")
df.24$NROB = 24
df.24 <- remove.glitch(df.24)


df <- rbind(df.8, df.16, df.24)
df$NROB <- as.factor(df$NROB)

df$CHAINDATASIZE <- df$CHAINDATASIZE / 100000

plot.line(df, "TIME", "CHAINDATASIZE", "Time (in seconds)", "Blockchain Size in MB", blockchain_size_file, ".",
    custom.base.breaks.x=c(0, 5000, 10000),
                        custom.base.breaks.y=c(0, 5, 10, 15, 20, 25))

plot.line(df.estimate, "TIME", "MEAN", "Time (in seconds)", "Swarm estimate", estimate_file, ".",
    custom.base.breaks.x=c(0, 5000, 10000),
                        custom.base.breaks.y=seq(0, 0.5, 0.1))


EXP = "G8"
estimate_file_8 = "/home/volker/final_data/data/Experiment_G8/8rob-2byz-1/214/sc.csv"
estimate_file_16 = "/home/volker/final_data/data/Experiment_G8/16rob-4byz-1/108/sc.csv"
estimate_file_24 = "/home/volker/final_data/data/Experiment_G8/24rob-6byz-1/215/sc.csv"
csv_file = paste0("combined_", EXP, ".csv")
csv_file_8 = "/home/volker/final_data/data/Experiment_G8/8rob-2byz-1/214/extra.csv"
csv_file_16 = "/home/volker/final_data/data/Experiment_G8/16rob-4byz-1/108/extra.csv"
csv_file_24 = "/home/volker/final_data/data/Experiment_G8/24rob-6byz-1/215/extra.csv"
estimate_file = paste0("estimate_file", EXP, ".png")
blockchain_size_file = paste0("blockchain_size", EXP, ".png")


df.8 <- read.csv(csv_file_8, sep=" ")
df.8$NROB = 8
df.8 <- remove.glitch(df.8)
df.16 <- read.csv(csv_file_16, sep=" ")
df.16$NROB = 16
df.16 <- remove.glitch(df.16)
df.24 <- read.csv(csv_file_24, sep=" ")
df.24$NROB = 24
df.24 <- remove.glitch(df.24)

df <- rbind(df.8, df.16, df.24)
df$NROB <- as.factor(df$NROB)

df$CHAINDATASIZE <- df$CHAINDATASIZE / 100000

df.8.estimate <- read.csv(estimate_file_8, sep=" ")
df.8.estimate$NROB = 8
df.16.estimate <- read.csv(estimate_file_16, sep=" ")
df.16.estimate$NROB = 16
df.24.estimate <- read.csv(estimate_file_24, sep=" ")
df.24.estimate$NROB = 24

df.estimate <- rbind(df.8.estimate, df.16.estimate, df.24.estimate)
df.estimate$MEAN <- df.estimate$MEAN / 10000000
df.estimate$NROB <- as.factor(df.estimate$NROB)
df.estimate <- df.estimate[df.estimate$MEAN != 0,]
df.estimate$TIME <- df.estimate$TIME
#print(df$CHAINDATASIZE)
#print(df$TIME)
#print(head(df))

plot.line(df, "TIME", "CHAINDATASIZE", "Time (in seconds)", "Blockchain Size in MB", blockchain_size_file, ".",
    custom.base.breaks.x=c(0, 5000, 10000),
                        custom.base.breaks.y=c(0, 5, 10, 15, 20, 25))

plot.line(df.estimate, "TIME", "MEAN", "Time (in seconds)", "Swarm estimate", estimate_file, ".",
    custom.base.breaks.x=c(0, 5000, 10000),
                        custom.base.breaks.y=seq(0, 0.5, 0.1))