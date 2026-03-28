## Extrai estatísticas completas das regressões da Fig.5
library(dplyr)

csv_path <- normalizePath(file.path("..", "figuras", "fig5_stress_data.csv"))
df <- read.csv(csv_path)
df$time_yr <- factor(df$time_yr, levels = c(0, 5, 10))

select_best_model <- function(data, yvar) {
  mod_lin  <- lm(reformulate("z_mid", yvar), data = data)
  mod_quad <- lm(reformulate("poly(z_mid, 2, raw = TRUE)", yvar), data = data)
  ftest <- anova(mod_lin, mod_quad)
  p_val <- ftest$`Pr(>F)`[2]
  list(
    mod_lin  = mod_lin,
    mod_quad = mod_quad,
    f_stat   = ftest$F[2],
    p_anova  = p_val,
    best     = if (!is.na(p_val) && p_val < 0.05) "quadratico" else "linear"
  )
}

cat("=" , rep("=", 70), "\n", sep = "")
cat("ESTATÍSTICAS DE REGRESSÃO — Fig. 5\n")
cat("Segmento MED / P95 / pessimista\n")
cat(rep("=", 71), "\n\n", sep = "")

for (tl in levels(df$time_yr)) {
  sub <- df %>% filter(time_yr == tl)
  cat(sprintf("── t = %s anos ──\n", tl))

  for (vv in c("sigma", "tau")) {
    vv_label <- ifelse(vv == "sigma", "σ_b (flexão)", "τ_s (cisalhamento)")
    res <- select_best_model(sub, vv)

    cat(sprintf("\n  %s:\n", vv_label))

    # Linear
    s_lin <- summary(res$mod_lin)
    cat(sprintf("    Linear:  R² = %.4f, R²adj = %.4f, F(%d,%d) = %.2f, p = %.4f\n",
                s_lin$r.squared, s_lin$adj.r.squared,
                s_lin$fstatistic[2], s_lin$fstatistic[3],
                s_lin$fstatistic[1], pf(s_lin$fstatistic[1], s_lin$fstatistic[2], s_lin$fstatistic[3], lower.tail=FALSE)))
    coef_lin <- coef(res$mod_lin)
    cat(sprintf("      β₀ = %.6f, β₁ = %.6f\n", coef_lin[1], coef_lin[2]))
    cat(sprintf("      Eq: %s = %.4f + %.4f·z\n", vv, coef_lin[1], coef_lin[2]))

    # Quadrático
    s_quad <- summary(res$mod_quad)
    cat(sprintf("    Quadrático: R² = %.4f, R²adj = %.4f, F(%d,%d) = %.2f, p = %.4f\n",
                s_quad$r.squared, s_quad$adj.r.squared,
                s_quad$fstatistic[2], s_quad$fstatistic[3],
                s_quad$fstatistic[1], pf(s_quad$fstatistic[1], s_quad$fstatistic[2], s_quad$fstatistic[3], lower.tail=FALSE)))
    coef_quad <- coef(res$mod_quad)
    cat(sprintf("      β₀ = %.6f, β₁ = %.6f, β₂ = %.6f\n", coef_quad[1], coef_quad[2], coef_quad[3]))
    cat(sprintf("      Eq: %s = %.4f + %.4f·z + %.4f·z²\n", vv, coef_quad[1], coef_quad[2], coef_quad[3]))

    # ANOVA comparativa
    cat(sprintf("    ANOVA (lin vs quad): F = %.3f, p = %.4f → MELHOR: %s\n",
                ifelse(is.na(res$f_stat), 0, res$f_stat),
                ifelse(is.na(res$p_anova), 1, res$p_anova),
                res$best))
  }
  cat("\n")
}
