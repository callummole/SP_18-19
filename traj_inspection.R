

library("tidyverse")
data = read_csv("Data/Midline_80_1.csv")

head(data)

ggplot(filter(data, World_z > 15), aes(x = YawRate_seconds)) + geom_histogram()

data %>% 
  filter(World_z > 15) %>% 
  summarise(mean = mean(YawRate_seconds),
            median = median(YawRate_seconds),
    iqr = IQR(YawRate_seconds))
