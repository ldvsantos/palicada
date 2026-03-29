## ---------------------------------------------------------------
## Fig. 4 — Safety factor (SF) evolution over time (EN version)
## 3 segments (INF, MED, SUP) / P95 / pessimistic
## Model selection: linear, quadratic, exponential (AIC)
## ---------------------------------------------------------------

library(ggplot2)
library(dplyr)
library(patchwork)
library(minpack.lm)

# ---- Paths ----
script_dir <- tryCatch(
  dirname(normalizePath(sys.frame(1)$ofile)),
  error = function(e) normalizePath(".")
)
base_dir <- normalizePath(file.path(script_dir, ".."), winslash = "/")
fig_dir  <- file.path(base_dir, "figuras", "versao_EN")
data_dir <- file.path(base_dir, "figuras")

dir.create(fig_dir, showWarnings = FALSE, recursive = TRUE)

df <- read.csv(file.path(data_dir, "fig4_safety_factor_data.csv"))

# Segment label with width
seg_labels <- df %>%
  distinct(segment, width_m) %>%
  mutate(seg_label = sprintf("%s (L = %.1f m)", segment, width_m))
df <- df %>% left_join(seg_labels, by = c("segment", "width_m"))
df$seg_label <- factor(df$seg_label, levels = seg_labels$seg_label)

# ---- Model selection per segment ----
select_best_model <- function(data) {
  y <- data$safety_factor
  x <- data$time_yr

  vary_idx <- which(y < 49.9)
  if (length(vary_idx) < 3) {
    return(list(model = "constant", r2 = NA,
                predict_fn = function(xnew) rep(mean(y), length(xnew)),
                eq = sprintf("SF ≈ %.1f (plateau)", mean(y)),
                data_fit = data))
  }

  sub <- data[vary_idx, ]
  x_sub <- sub$time_yr
  y_sub <- sub$safety_factor

  mod_lin <- lm(safety_factor ~ time_yr, data = sub)
  aic_lin <- AIC(mod_lin)
  r2_lin  <- summary(mod_lin)$r.squared

  mod_quad <- lm(safety_factor ~ poly(time_yr, 2, raw = TRUE), data = sub)
  aic_quad <- AIC(mod_quad)
  r2_quad  <- summary(mod_quad)$r.squared

  aic_exp <- Inf; r2_exp <- 0; mod_exp <- NULL
  tryCatch({
    start_a <- max(y_sub)
    start_b <- log(min(y_sub[y_sub > 0]) / start_a) / max(x_sub)
    mod_exp <- nlsLM(safety_factor ~ a * exp(b * time_yr), data = sub,
                     start = list(a = start_a, b = start_b),
                     control = nls.lm.control(maxiter = 200))
    ss_res <- sum(residuals(mod_exp)^2)
    ss_tot <- sum((y_sub - mean(y_sub))^2)
    r2_exp <- 1 - ss_res / ss_tot
    aic_exp <- AIC(mod_exp)
  }, error = function(e) {
    aic_exp <<- Inf
    r2_exp  <<- 0
    mod_exp <<- NULL
  })

  aics <- c(linear = aic_lin, quadratic = aic_quad, exponential = aic_exp)
  best_name <- names(which.min(aics))

  if (best_name == "exponential" && !is.null(mod_exp)) {
    co <- coef(mod_exp)
    list(model = "exponential", r2 = r2_exp,
         predict_fn = function(xnew) co["a"] * exp(co["b"] * xnew),
         eq = sprintf("SF = %.2f·exp(%.3f·t)", co["a"], co["b"]),
         t_start = min(x_sub))
  } else if (best_name == "quadratic") {
    co <- coef(mod_quad)
    list(model = "quadratic", r2 = r2_quad,
         predict_fn = function(xnew) predict(mod_quad, newdata = data.frame(time_yr = xnew)),
         eq = sprintf("SF = %.2f + %.2f·t + %.4f·t²", co[1], co[2], co[3]),
         t_start = min(x_sub))
  } else {
    co <- coef(mod_lin)
    list(model = "linear", r2 = r2_lin,
         predict_fn = function(xnew) predict(mod_lin, newdata = data.frame(time_yr = xnew)),
         eq = sprintf("SF = %.2f + %.3f·t", co[1], co[2]),
         t_start = min(x_sub))
  }
}

# Generate predictions and annotations
pred_list  <- list()
annot_list <- list()

for (sl in unique(df$seg_label)) {
  sub <- df %>% filter(seg_label == sl)
  best <- select_best_model(sub)

  if (is.na(best$r2)) {
    x_grid <- seq(min(sub$time_yr), max(sub$time_yr), length.out = 300)
    y_hat  <- best$predict_fn(x_grid)
  } else {
    t_start <- best$t_start
    plat_x <- seq(min(sub$time_yr), t_start, length.out = 50)
    plat_y <- rep(50, length(plat_x))
    curve_x <- seq(t_start, max(sub$time_yr), length.out = 250)
    curve_y <- best$predict_fn(curve_x)
    x_grid <- c(plat_x, curve_x)
    y_hat  <- c(plat_y, curve_y)
  }

  pred_list[[sl]] <- data.frame(
    time_yr = x_grid, safety_factor = y_hat, seg_label = sl
  )
  annot_list[[sl]] <- data.frame(
    seg_label = sl, r2 = best$r2, model = best$model, eq = best$eq
  )
}

pred_df  <- bind_rows(pred_list)
annot_df <- bind_rows(annot_list)

annot_df <- annot_df %>%
  mutate(label = ifelse(is.na(r2),
                        sprintf("%s (plateau)", seg_label),
                        sprintf("%s (R² = %.3f)", seg_label, r2)))
label_map <- setNames(annot_df$label, annot_df$seg_label)

# ---- Academic theme ----
theme_academic <- theme_classic(base_size = 12, base_family = "serif") +
  theme(
    axis.title       = element_text(size = 11),
    legend.position  = "bottom",
    legend.title     = element_blank(),
    legend.text      = element_text(size = 9),
    panel.grid.major = element_line(colour = "grey90", linewidth = 0.3),
    plot.margin      = margin(5, 10, 5, 5)
  )

colors_seg <- c("#2ca02c", "#d62728", "#1f77b4")
names(colors_seg) <- levels(df$seg_label)
shapes_seg <- c(15, 16, 17)
names(shapes_seg) <- levels(df$seg_label)

# ---- Plot ----
p <- ggplot() +
  geom_point(data = df, aes(x = time_yr, y = safety_factor,
                             colour = seg_label, shape = seg_label),
             size = 2.5, stroke = 0.6) +
  geom_path(data = pred_df, aes(x = time_yr, y = safety_factor,
                                 colour = seg_label, linetype = seg_label),
            linewidth = 0.9) +
  geom_hline(yintercept = 1.5, colour = "grey50", linetype = "dashed", linewidth = 0.6) +
  geom_hline(yintercept = 1.0, colour = "black", linetype = "dotted", linewidth = 0.6) +
  annotate("text", x = 0.3, y = 1.7, label = "SF = 1.5", size = 3,
           colour = "grey40", family = "serif") +
  scale_colour_manual(values = colors_seg,
                      labels = function(x) label_map[x]) +
  scale_shape_manual(values = shapes_seg,
                     labels = function(x) label_map[x]) +
  scale_linetype_manual(values = c("solid", "dashed", "dotdash"),
                        labels = function(x) label_map[x]) +
  scale_y_log10(limits = c(0.8, 200)) +
  coord_cartesian(xlim = c(0, 10)) +
  labs(x = "Time (years)",
       y = expression("Safety factor (1 / FI"["max"]*")")) +
  theme_academic

# Add equations
eq_lines <- annot_df %>% filter(!is.na(r2))
eq_text <- paste(eq_lines$eq, collapse = "\n")
p <- p + annotate("text", x = 7.5, y = 150, label = eq_text,
                   size = 2.8, hjust = 0.5, family = "serif",
                   colour = "grey30")

ggsave(file.path(fig_dir, "Fig_3_safety_factor.png"), p,
       width = 8, height = 5, dpi = 300, bg = "white")
ggsave(file.path(fig_dir, "Fig_3_safety_factor.pdf"), p,
       width = 8, height = 5, bg = "white")

cat("\n=== EN figures saved to:", fig_dir, "===\n")
