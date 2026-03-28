## ---------------------------------------------------------------
## Fig. 5 — Distribuição vertical de tensões (σ_b e τ_s)
## Segmento MED / P95 / pessimista
## Regressão com seleção de modelo (linear vs quadrático, ANOVA)
## ---------------------------------------------------------------

library(ggplot2)
library(dplyr)
library(tidyr)
library(patchwork)

# ---- Caminhos ----
script_dir <- tryCatch(
  dirname(normalizePath(sys.frame(1)$ofile)),
  error = function(e) normalizePath(".")
)
base_dir <- normalizePath(file.path(script_dir, ".."), winslash = "/")
fig_dir  <- file.path(base_dir, "figuras")
csv_path <- file.path(fig_dir, "fig5_stress_data.csv")

df <- read.csv(csv_path)
df$time_yr <- factor(df$time_yr, levels = c(0, 5, 10),
                     labels = c("t = 0 anos", "t = 5 anos", "t = 10 anos"))

# ---- Seleção de modelo por série (ANOVA: linear vs quadrático) ----
select_best_model <- function(data, yvar) {
  mod_lin  <- lm(reformulate("z_mid", yvar), data = data)
  mod_quad <- lm(reformulate("poly(z_mid, 2, raw = TRUE)", yvar), data = data)
  ftest <- anova(mod_lin, mod_quad)
  p_val <- ftest$`Pr(>F)`[2]
  if (!is.na(p_val) && p_val < 0.05) mod_quad else mod_lin
}

# Gerar predições por série
pred_list <- list()
annot_list <- list()

for (tl in levels(df$time_yr)) {
  sub <- df %>% filter(time_yr == tl)
  z_grid <- data.frame(z_mid = seq(min(sub$z_mid), max(sub$z_mid), length.out = 200))

  for (vv in c("sigma", "tau")) {
    mod_lin  <- lm(reformulate("z_mid", vv), data = sub)
    mod_quad <- lm(reformulate("poly(z_mid, 2, raw = TRUE)", vv), data = sub)
    ftest <- anova(mod_lin, mod_quad)
    p_val <- ftest$`Pr(>F)`[2]
    best <- if (!is.na(p_val) && p_val < 0.05) mod_quad else mod_lin

    r2  <- summary(best)$r.squared
    deg <- length(coef(best)) - 1
    cc  <- coef(best)
    yhat <- predict(best, newdata = z_grid)

    # Montar equação como texto
    if (deg == 1) {
      eq_txt <- sprintf("y = %.2f + %.2f z", cc[1], cc[2])
    } else {
      eq_txt <- sprintf("y = %.2f %+.2f z %+.2f z\u00b2", cc[1], cc[2], cc[3])
    }

    pred_list[[paste(tl, vv)]] <- data.frame(
      z_mid    = z_grid$z_mid,
      value    = yhat,
      variable = vv,
      time_yr  = tl
    )
    annot_list[[paste(tl, vv)]] <- data.frame(
      time_yr  = tl,
      variable = vv,
      r2       = r2,
      degree   = deg,
      eq_txt   = eq_txt,
      stringsAsFactors = FALSE
    )
  }
}

pred_df  <- bind_rows(pred_list)
annot_df <- bind_rows(annot_list)

# ---- Reshape dados observados para long ----
df_long <- df %>%
  pivot_longer(cols = c(sigma, tau), names_to = "variable", values_to = "value")

# Labels para facet
var_labels <- c(sigma = expression(sigma[b]~" (MPa)"),
                tau   = expression(tau[s]~" (MPa)"))

# Labels para legenda com R²
annot_df <- annot_df %>%
  mutate(label = sprintf("%s (R² = %.3f)", time_yr, r2))
label_map <- setNames(annot_df$label, paste(annot_df$time_yr, annot_df$variable))

pred_df <- pred_df %>%
  mutate(legend = label_map[paste(time_yr, variable)])
df_long <- df_long %>%
  mutate(legend = label_map[paste(time_yr, variable)])

# ---- Tema acadêmico ----
theme_academic <- theme_classic(base_size = 12, base_family = "serif") +
  theme(
    strip.background  = element_blank(),
    strip.text         = element_text(face = "bold", size = 12),
    axis.title         = element_text(size = 11),
    legend.position    = "bottom",
    legend.title       = element_blank(),
    legend.text        = element_text(size = 9),
    panel.grid.major   = element_line(colour = "grey90", linewidth = 0.3),
    plot.margin        = margin(5, 10, 5, 5)
  )

shapes <- c("t = 0 anos" = 16, "t = 5 anos" = 15, "t = 10 anos" = 17)

# Função auxiliar para montar labels com R² por painel
make_labels <- function(var_name) {
  function(x) {
    sapply(x, function(t) {
      a <- annot_df %>% filter(time_yr == t, variable == var_name)
      sprintf("%s (R² = %.3f)", t, a$r2)
    })
  }
}

# Função de escalas comuns
add_scales <- function(var_name) {
  list(
    scale_colour_manual(values = c("#1b9e77", "#d95f02", "#7570b3"),
                        labels = make_labels(var_name)),
    scale_shape_manual(values = shapes, labels = make_labels(var_name)),
    scale_linetype_manual(values = c("solid", "dashed", "dotdash"),
                          labels = make_labels(var_name))
  )
}

# ---- Painel (a) σ_b ----
df_sig  <- df_long  %>% filter(variable == "sigma")
pr_sig  <- pred_df  %>% filter(variable == "sigma") %>% arrange(time_yr, z_mid)
eq_sig  <- annot_df %>% filter(variable == "sigma") %>%
  mutate(label = sprintf("%s\n%s   R² = %.3f", time_yr, eq_txt, r2))

# Posição das anotações (canto superior esquerdo, empilhadas)
x_pos <- min(df_sig$value) + 0.02 * diff(range(df_sig$value))
eq_sig$x <- x_pos
eq_sig$y <- max(df_sig$z_mid) - (0:(nrow(eq_sig)-1)) * 0.12

p1 <- ggplot() +
  geom_point(data = df_sig, aes(x = value, y = z_mid,
                                colour = time_yr, shape = time_yr),
             size = 2.8, stroke = 0.7) +
  geom_path(data = pr_sig, aes(x = value, y = z_mid,
                               colour = time_yr, linetype = time_yr),
            linewidth = 0.9) +
  geom_text(data = eq_sig, aes(x = x, y = y, label = label, colour = time_yr),
            hjust = 0, vjust = 1, size = 2.8, family = "serif", show.legend = FALSE) +
  add_scales("sigma") +
  labs(x = expression(sigma[b]~" (MPa)"), y = "Altura z (m)",
       tag = "(a)") +
  ggtitle("Tensão de flexão") +
  theme_academic

# ---- Painel (b) τ_s ----
df_tau  <- df_long  %>% filter(variable == "tau")
pr_tau  <- pred_df  %>% filter(variable == "tau") %>% arrange(time_yr, z_mid)
eq_tau  <- annot_df %>% filter(variable == "tau") %>%
  mutate(label = sprintf("%s\n%s   R² = %.3f", time_yr, eq_txt, r2))

x_pos_t <- max(df_tau$value) - 0.02 * diff(range(df_tau$value))
eq_tau$x <- x_pos_t
eq_tau$y <- max(df_tau$z_mid) - (0:(nrow(eq_tau)-1)) * 0.12

p2 <- ggplot() +
  geom_point(data = df_tau, aes(x = value, y = z_mid,
                                colour = time_yr, shape = time_yr),
             size = 2.8, stroke = 0.7) +
  geom_path(data = pr_tau, aes(x = value, y = z_mid,
                               colour = time_yr, linetype = time_yr),
            linewidth = 0.9) +
  geom_text(data = eq_tau, aes(x = x, y = y, label = label, colour = time_yr),
            hjust = 1, vjust = 1, size = 2.8, family = "serif", show.legend = FALSE) +
  add_scales("tau") +
  labs(x = expression(tau[s]~" (MPa)"), y = NULL,
       tag = "(b)") +
  ggtitle("Tensão de cisalhamento") +
  theme_academic

# ---- Composição final ----
fig <- p1 + p2 +
  plot_layout(guides = "collect") &
  theme(legend.position = "bottom")

ggsave(file.path(fig_dir, "Fig_5_stress_height.png"), fig,
       width = 10, height = 5, dpi = 300, bg = "white")
ggsave(file.path(fig_dir, "Fig_5_stress_height.pdf"), fig,
       width = 10, height = 5, bg = "white")

cat("Fig_5_stress_height salva em:", fig_dir, "\n")
