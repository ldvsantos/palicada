## ---------------------------------------------------------------
## Fig. 6 — FI nodal vs internodal + razão de concentração
## Segmento MED / P95 / pessimista
## Seleção de modelo: linear, quadrático, exponencial (AIC)
## ---------------------------------------------------------------

library(ggplot2)
library(dplyr)
library(tidyr)
library(patchwork)
library(minpack.lm)

# ---- Caminhos ----
script_dir <- tryCatch(
  dirname(normalizePath(sys.frame(1)$ofile)),
  error = function(e) normalizePath(".")
)
base_dir <- normalizePath(file.path(script_dir, ".."), winslash = "/")
fig_dir  <- file.path(base_dir, "figuras")

df <- read.csv(file.path(fig_dir, "fig6_node_zone_data.csv"))

# ---- Seleção de modelo (AIC: linear vs quadrático vs exponencial) ----
select_best <- function(x, y, yname = "y") {
  data <- data.frame(x = x, y = y)

  # Linear
  mod_lin  <- lm(y ~ x, data = data)
  aic_lin  <- AIC(mod_lin)
  r2_lin   <- summary(mod_lin)$r.squared

  # Quadrático
  mod_quad <- lm(y ~ poly(x, 2, raw = TRUE), data = data)
  aic_quad <- AIC(mod_quad)
  r2_quad  <- summary(mod_quad)$r.squared

  # Exponencial: y = a * exp(b * x)
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

# ---- Ajustes ----
fit_nodal <- select_best(df$time_yr, df$fi_nodal, "FI_nodal")
fit_inter <- select_best(df$time_yr, df$fi_internodal, "FI_inter")
fit_ratio <- select_best(df$time_yr, df$ratio, "Razão")

t_grid <- seq(min(df$time_yr), max(df$time_yr), length.out = 300)

pred_fi <- data.frame(
  time_yr = rep(t_grid, 2),
  FI = c(fit_nodal$predict_fn(t_grid), fit_inter$predict_fn(t_grid)),
  zona = rep(c("Zona nodal", "Zona internodal"), each = length(t_grid))
)

pred_ratio <- data.frame(
  time_yr = t_grid,
  ratio = fit_ratio$predict_fn(t_grid)
)

# Reshape observados para long
df_long <- df %>%
  select(time_yr, fi_nodal, fi_internodal) %>%
  pivot_longer(cols = c(fi_nodal, fi_internodal),
               names_to = "zona", values_to = "FI") %>%
  mutate(zona = recode(zona,
                       fi_nodal = "Zona nodal",
                       fi_internodal = "Zona internodal"))

# ---- Tema acadêmico ----
theme_academic <- theme_classic(base_size = 12, base_family = "serif") +
  theme(
    axis.title       = element_text(size = 11),
    legend.position  = "bottom",
    legend.title     = element_blank(),
    legend.text      = element_text(size = 9),
    panel.grid.major = element_line(colour = "grey90", linewidth = 0.3),
    plot.margin      = margin(5, 10, 5, 5)
  )

colors_zona <- c("Zona nodal" = "#d62728", "Zona internodal" = "#2ca02c")
shapes_zona <- c("Zona nodal" = 16, "Zona internodal" = 15)

# Labels com R²
lbl_nodal <- sprintf("Zona nodal (R² = %.3f)", fit_nodal$r2)
lbl_inter <- sprintf("Zona internodal (R² = %.3f)", fit_inter$r2)
label_map <- c("Zona nodal" = lbl_nodal, "Zona internodal" = lbl_inter)

# ---- Painel (a): FI nodal vs internodal ----
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
  labs(x = "Tempo (anos)", y = expression("FI"["max"]~"(Tsai-Hill)"),
       tag = "(a)") +
  theme_academic

# ---- Painel (b): Razão nodal/internodal ----
lbl_ratio <- sprintf("Razão (R² = %.3f)", fit_ratio$r2)

p2 <- ggplot() +
  geom_point(data = df, aes(x = time_yr, y = ratio),
             size = 2.5, stroke = 0.6, colour = "grey40", shape = 18) +
  geom_path(data = pred_ratio, aes(x = time_yr, y = ratio),
            linewidth = 0.9, colour = "grey40", linetype = "solid") +
  labs(x = "Tempo (anos)", y = "Razão nodal / internodal (×)",
       tag = "(b)") +
  annotate("text", x = 1, y = max(df$ratio) * 0.98,
           label = lbl_ratio, size = 3.2, hjust = 0, family = "serif",
           colour = "grey30") +
  theme_academic

# ---- Composição ----
fig <- p1 + p2 + plot_layout(widths = c(1.2, 1))

ggsave(file.path(fig_dir, "Fig_7_node_zone.png"), fig,
       width = 12, height = 5, dpi = 300, bg = "white")
ggsave(file.path(fig_dir, "Fig_7_node_zone.pdf"), fig,
       width = 12, height = 5, bg = "white")

# ---- Resumo estatístico ----
cat("\n=== Resumo estatístico — Fig. 6 (Nodal/Internodal) ===\n")
cat(sprintf("  Nodal:       modelo %s, R² = %.4f, %s\n",
            fit_nodal$model, fit_nodal$r2, fit_nodal$eq))
cat(sprintf("  Internodal:  modelo %s, R² = %.4f, %s\n",
            fit_inter$model, fit_inter$r2, fit_inter$eq))
cat(sprintf("  Razão:       modelo %s, R² = %.4f, %s\n",
            fit_ratio$model, fit_ratio$r2, fit_ratio$eq))
cat("Fig_7_node_zone salva em:", fig_dir, "\n")
