## ---------------------------------------------------------------
## Fig. 3 — Evolução temporal do índice de Tsai-Hill (FI_max)
## Segmento MED / 3 cenários de degradação × 2 cenários hidrológicos
## Seleção de modelo: linear, quadrático, exponencial (AIC)
## ---------------------------------------------------------------

library(ggplot2)
library(dplyr)
library(minpack.lm)

# ---- Caminhos ----
script_dir <- tryCatch(
  dirname(normalizePath(sys.frame(1)$ofile)),
  error = function(e) normalizePath(".")
)
base_dir <- normalizePath(file.path(script_dir, ".."), winslash = "/")
fig_dir  <- file.path(base_dir, "figuras")

df <- read.csv(file.path(fig_dir, "fig3_fi_evolution_data.csv"))

# ---- Seleção de modelo (AIC: linear vs quadrático vs exponencial) ----
select_best <- function(x, y, yname = "FI") {
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

# ---- Ajustar modelo para cada combinação degradação × hidro ----
combos <- df %>% distinct(degradation, hydro)
t_grid <- seq(min(df$time_yr), max(df$time_yr), length.out = 300)

fits <- list()
pred_list <- list()

for (i in seq_len(nrow(combos))) {
  deg <- combos$degradation[i]
  hyd <- combos$hydro[i]
  sub <- df %>% filter(degradation == deg, hydro == hyd) %>% arrange(time_yr)
  key <- paste(deg, hyd, sep = "_")

  fit <- select_best(sub$time_yr, sub$max_FI, sprintf("FI[%s,%s]", deg, hyd))
  fits[[key]] <- fit

  pred_list[[key]] <- data.frame(
    time_yr     = t_grid,
    max_FI      = fit$predict_fn(t_grid),
    degradation = deg,
    hydro       = hyd
  )
}

pred_all <- bind_rows(pred_list)

# ---- Labels de legenda ----
deg_labels_pt <- c(optimistic = "Otimista", baseline = "Referência",
                   pessimistic = "Pessimista")

# Construir label com R²
df$series <- paste(df$degradation, df$hydro, sep = "_")
pred_all$series <- paste(pred_all$degradation, pred_all$hydro, sep = "_")

make_label <- function(deg, hyd) {
  key <- paste(deg, hyd, sep = "_")
  fit <- fits[[key]]
  sprintf("%s · %s (R² = %.3f)", deg_labels_pt[deg], hyd, fit$r2)
}

label_map <- setNames(
  mapply(make_label, combos$degradation, combos$hydro, SIMPLIFY = TRUE),
  paste(combos$degradation, combos$hydro, sep = "_")
)

df$label       <- label_map[df$series]
pred_all$label <- label_map[pred_all$series]

# Ordenar factor para legenda consistente
lev_order <- c("optimistic_P95", "optimistic_median",
               "baseline_P95", "baseline_median",
               "pessimistic_P95", "pessimistic_median")
df$label       <- factor(df$label, levels = label_map[lev_order])
pred_all$label <- factor(pred_all$label, levels = label_map[lev_order])

# ---- Cores e formas ----
keys <- c("optimistic_P95", "optimistic_median",
          "baseline_P95", "baseline_median",
          "pessimistic_P95", "pessimistic_median")

colors_series <- setNames(
  c("#2ca02c", "#2ca02c", "#ff7f0e", "#ff7f0e", "#d62728", "#d62728"),
  label_map[keys]
)

shapes_series <- setNames(
  c(16, 1, 17, 2, 15, 0),
  label_map[keys]
)

linetypes_series <- setNames(
  c("solid", "dashed", "solid", "dashed", "solid", "dashed"),
  label_map[keys]
)

# ---- Tema acadêmico ----
theme_academic <- theme_classic(base_size = 12, base_family = "serif") +
  theme(
    axis.title       = element_text(size = 11),
    legend.position  = "bottom",
    legend.title     = element_blank(),
    legend.text      = element_text(size = 8),
    panel.grid.major = element_line(colour = "grey90", linewidth = 0.3),
    plot.margin      = margin(5, 10, 5, 5)
  )

# ---- Plot ----
p <- ggplot() +
  # Pontos observados
  geom_point(data = df,
             aes(x = time_yr, y = max_FI, colour = label, shape = label),
             size = 2, stroke = 0.5) +
  # Curvas de regressão (P95: linewidth maior)
  geom_path(data = pred_all %>% filter(hydro == "P95"),
            aes(x = time_yr, y = max_FI, colour = label, linetype = label),
            linewidth = 0.9) +
  geom_path(data = pred_all %>% filter(hydro == "median"),
            aes(x = time_yr, y = max_FI, colour = label, linetype = label),
            linewidth = 0.6) +
  # Linha de falha FI = 1.0
  geom_hline(yintercept = 1.0, colour = "black", linetype = "dotted",
             linewidth = 0.6) +
  annotate("text", x = 0.3, y = 1.05, label = "FI = 1 (falha)",
           size = 3, family = "serif", hjust = 0) +
  scale_colour_manual(values = colors_series) +
  scale_shape_manual(values = shapes_series) +
  scale_linetype_manual(values = linetypes_series) +
  guides(colour = guide_legend(ncol = 2, override.aes = list(linewidth = 0.8))) +
  labs(x = "Tempo (anos)",
       y = expression("FI"["max"]~"(Tsai-Hill)")) +
  coord_cartesian(xlim = c(0, 10)) +
  theme_academic

# ---- Salvar ----
ggsave(file.path(fig_dir, "Fig_2_fi_evolution_MED.png"), p,
       width = 9, height = 6, dpi = 300, bg = "white")
ggsave(file.path(fig_dir, "Fig_2_fi_evolution_MED.pdf"), p,
       width = 9, height = 6, bg = "white")

# ---- Resumo estatístico ----
cat("\n=== Resumo estatístico — Fig. 3 (FI evolution MED) ===\n")
for (key in names(fits)) {
  f <- fits[[key]]
  cat(sprintf("  %s: modelo %s, R² = %.4f, %s\n", key, f$model, f$r2, f$eq))
}
cat("Figuras salvas em:", fig_dir, "\n")
