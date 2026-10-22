library(tidyverse)
library(lubridate)

data <- read_csv("data/vehicle_data_clean.csv")

glimpse(data)

data <- data %>% 
    mutate(
        timestamp = ymd_hms(timestamp),
        date = as.Date(timestamp),
        time = format(timestamp, "%H:%M:%S%"),
        day_of_week = wday(timestamp, label = TRUE)
    )


summary(data)

count(data, mode)

data %>%
    group_by(mode) %>%
    summarise(
        observations = n(),
        mean_delay = mean(delay_seconds, na.rm = TRUE),
        median_delay = median(delay_seconds, na.rm = TRUE),
        sd_delay = sd(delay_seconds, na.rm = TRUE)
    )

ggplot(data, aes(x = delay_seconds)) +
  geom_histogram(bins = 50) +
  labs(
    title = "Distribution of Public Transit Delays in Prague",
    x = "Delay (Seconds)",
    y = "Number of Observations"
  )

route_summary <- data %>%
  group_by(mode, route) %>%
  summarise(
    observations = n(),
    mean_delay = mean(delay_seconds, na.rm = TRUE),
    median_delay = median(delay_seconds, na.rm = TRUE),
    sd_delay = sd(delay_seconds, na.rm = TRUE),
    pct_over_2min = mean(delay_seconds > 120, na.rm = TRUE) * 100,
    pct_over_5min = mean(delay_seconds > 300, na.rm = TRUE) * 100,
    .groups = "drop"
  ) %>%
  arrange(desc(median_delay))

route_summary

ggplot(
  route_summary %>% 
    filter(observations >= 100),
  aes(
    x = reorder(route, median_delay),
    y = median_delay
  )
) +
  geom_col() +
  coord_flip() +
  labs(
    title = "Median Transit Delay by Route",
    x = "Route",
    y = "Median Delay (seconds)"
  ) +
  theme_minimal()

data %>%
  arrange(desc(delay_seconds)) %>%
  select(
    timestamp,
    vehicle_id,
    trip_id,
    route,
    mode,
    delay_seconds,
    status
  ) %>%
  head(20)

ggplot(data, aes(x = delay_seconds)) +
  geom_histogram(bins = 50) +
  labs(
    title = "Distribution of Transit Delays",
    x = "Delay (seconds)",
    y = "Number of observations"
  ) +
  theme_minimal()

ggplot(
  data %>% filter(delay_seconds >= -300, delay_seconds <= 900),
  aes(x = delay_seconds)
) +
  geom_histogram(bins = 50) +
  labs(
    title = "Distribution of Transit Delays",
    x = "Delay (seconds)",
    y = "Number of observations"
  ) +
  theme_minimal()

trip_summary <- data %>%
  group_by(vehicle_id, trip_id, route, mode) %>%
  summarise(
    observations = n(),
    duration_minutes = as.numeric(
      difftime(max(timestamp), min(timestamp), units = "mins")
    ),
    valid_delay_observations = sum(!is.na(delay_seconds)),
    mean_delay = if (all(is.na(delay_seconds))) NA_real_ else mean(delay_seconds, na.rm = TRUE),
    median_delay = if (all(is.na(delay_seconds))) NA_real_ else median(delay_seconds, na.rm = TRUE),
    sd_delay = if (sum(!is.na(delay_seconds)) < 2) NA_real_ else sd(delay_seconds, na.rm = TRUE),
    min_delay = if (all(is.na(delay_seconds))) NA_real_ else min(delay_seconds, na.rm = TRUE),
    max_delay = if (all(is.na(delay_seconds))) NA_real_ else max(delay_seconds, na.rm = TRUE),
    pct_over_2min = if (all(is.na(delay_seconds))) NA_real_ else mean(delay_seconds > 120, na.rm = TRUE) * 100,
    pct_over_5min = if (all(is.na(delay_seconds))) NA_real_ else mean(delay_seconds > 300, na.rm = TRUE) * 100,
    .groups = "drop"
  )
  