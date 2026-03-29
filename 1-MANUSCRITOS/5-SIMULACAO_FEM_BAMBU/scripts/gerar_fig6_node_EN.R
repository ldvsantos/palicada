## ---------------------------------------------------------------
## Fig. 6 — FI nodal vs internodal + concentration ratio (EN version)
## MED segment / P95 / pessimistic
## Model selection: linear, quadratic, exponential (AIC)
## ---------------------------------------------------------------

library(ggplot2)
library(dplyr)
library(tidyr)
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

df <- read.csv(file.path(data_dir, "fig6_node_zone_data.csv"))

# ---- Model selection (AIC: linear vs quadratic vs exponential) ----
select_best <- function(x, y, yname = "y") {
  data <- data.frame(x = x, y = y)

  mod_lin  <- lm(y ~ x, data = data)
  aic_lin  <- AIC(mod_lin)
  r2_lin   <- summary(mod_lin)$r.squared

  mod_quad <- lm(y ~ poly(x, 2, raw = TRUE), data = data)
  aic_quad <- AIC(mod_quad)
  r2_quad  <- summary(mod_quad)$r.squared

  aic_exp <- Inf; r2_exp <- 0; mod_exp <- NULL
  tryCatch({
    start_a <- min(y[y > 0])
    start_b <- log(max(y) / start_a) / max(x)
    mod_exp <- nlsLM(y ~ a * exp(b * x), data = data,
                     start = list(a = start_a, b = start_b),
                     control = nls.lm.control(maxiter = 200))
    ss_res <- sum(residuals(mod_exp)^2)
    ss_tot <- sum((y - mean(y))^2)
    r2_exp <- 1 - ss_res / ss_tot
    aic_exp <- AIC(mod_exp)
  }, error = function(e) {})

  aics <- c(linear = aic_lin, quadratic = aic_quad, exponential = aic_exp)
  best_name <- names(which.min(aics))

  if (best_name == "exponential" && !is.null(mod_exp)) {
    co <- coef(mod_exp)
    list(model = "exponential", r2 = r2_exp,
         predict_fn = function(xnew) co["a"] * exp(co["b"] * xnew),
         eq = sprintf("%s = %.4f·exp(%.3f·t)", yname, co["a"], co["b"]))
  } else if (best_name == "quadratic") {
    co <- coef(mod_quad)
    list(model = "quadratic", r2 = r2_quad,
         predict_fn = function(xnew) predict(mod_quad, newdata = data.frame(x = xnew)),
         eq = sprintf("%s = %.4f + %.4f·t + %.5f·t²", yname, co[1], co[2], co[3]))
  } else {
    co <- coef(mod_lin)
    list(model = "linear", r2 = r2_lin,
         predict_fn = function(xnew) predict(mod_lin, newdata = data.frame(x = xnew)),
         eq = sprintf("%s = %.4f + %.4f·t", yname, co[1], co[2]))
  }
}

# ---- Fits ----
fit_nodal <- select_best(df$time_yr, df$fi_nodal, "FI_nodal")
fit_inter <- select_best(df$time_yr, df$fi_internodal, "FI_inter")
fit_ratio <- select_best(df$time_yr, df$ratio, "Ratio")

t_grid <- seq(min(df$time_yr), max(df$time_yr), length.out = 300)

pred_fi <- data.frame(
  time_yr = rep(t_grid, 2),
  FI = c(fit_nodal$predict_fn(t_grid), fit_inter$predict_fn(t_grid)),
  zona = rep(c("Nodal zone", "Internodal zone"), each = length(t_grid))
)

pred_ratio <- data.frame(
  time_yr = t_grid,
  ratio = fit_ratio$predict_fn(t_grid)
)

# Reshape observed to long
df_long <- df %>%
  select(time_yr, fi_nodal, fi_internodal) %>%
  pivot_longer(cols = c(fi_nodal, fi_internodal),
               names_to = "zona", values_to = "FI") %>%
  mutate(zona = recode(zona,
                       fi_nodal = "Nodal zone",
                       fi_internodal = "Internodal zone"))

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

colors_zona <- c("Nodal zone" = "#d62728", "Internodal zone" = "#2ca02c")
shapes_zona <- c("Nodal zone" = 16, "Internodal zone" = 15)

# Labels with R²
lbl_nodal <- sprintf("Nodal zone (R² = %.3f)", fit_nodal$r2)
lbl_inter <- sprintf("Internodal zone (R² = %.3f)", fit_inter$r2)
label_map <- c("Nodal zone" = lbl_nodal, "Internodal zone" = lbl_inter)

# ---- Panel (a): FI nodal vs internodal ----
p1 <- ggplot() +
  geom_point(data = df_long, aes(x = time_yr, y = FI,
                                  colour = zona, shape = zona),
             size = 2.5, stroke = 0.6) +
  geom_path(data = pred_fi, aes(x = time_yr, y = FI,
                                 colour = zona, linetype = zona),
            linewidth = 0.9) +
  geom_hline(yintercept = 1.0, colour = "black", linetype = "dotted", linewidth = 0.6) +
  scale_colour_manual(values = colors_zona, labels = label_map) +
  scale_shape_manual(values = shapes_zona, labels = label_map) +
  scale_linetype_manual(values = c("solid", "dashed"), labels = label_map) +
  labs(x = "Time (years)", y = expression("FI"["max"]~"(Tsai-Hill)"),
       tag = "(a)") +
  theme_academic

# ---- Panel (b): Nodal/internodal ratio ----
lbl_ratio <- sprintf("Ratio (R² = %.3f)", fit_ratio$r2)

p2 <- ggplot() +
  geom_point(data = df, aes(x = time_yr, y = ratio),
             size = 2.5, stroke = 0.6, colour = "grey40", shape = 18) +
  geom_path(data = pred_ratio, aes(x = time_yr, y = ratio),
            linewidth = 0.9, colour = "grey40", linetype = "solid") +
  labs(x = "Time (years)", y = "Nodal/internodal ratio (\u00d7)",
       tag = "(b)") +
  annotate("text", x = 1, y = max(df$ratio) * 0.98,
           label = lbl_ratio, size = 3.2, hjust = 0, family = "serif",
           colour = "grey30") +
  theme_academic

# ---- Composition ----
fig <- p1 + p2 + plot_layout(widths = c(1.2, 1))

ggsave(file.path(fig_dir, "Fig_7_node_zone.png"), fig,
       width = 12, height = 5, dpi = 300, bg = "white")
ggsave(file.path(fig_dir, "Fig_7_node_zone.pdf"), fig,
       width = 12, height = 5, bg = "white")

cat("Fig_7_node_zone (EN) saved to:", fig_dir, "\n")
