from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "2-DADOS" / "Planilha_Sedimentos_talude.xlsx"
OUTPUT_XLSX = ROOT / "2-DADOS" / "Sedimentos_talude_LIMPO_PEDRA_organizado.xlsx"
OUTPUT_CSV = ROOT / "2-DADOS" / "Sedimentos_talude_LIMPO_PEDRA_dados_longos.csv"


def parse_number(value: object) -> float | None:
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    text = text.replace("\xa0", " ")
    text = re.sub(r"\([^)]*\)", "", text)

    matches = re.findall(r"\d+(?:[\.,]\d+)?", text)
    if not matches:
        return None

    number = matches[-1].replace(",", ".")
    try:
        return float(number)
    except ValueError:
        return None


def parse_collection_label(value: object, index: int) -> tuple[str, str | None]:
    label = f"Coleta_{index:02d}"
    date = None

    if pd.isna(value):
        return label, date

    text = str(value).strip()
    match_id = re.search(r"(\d+\s*A)", text, flags=re.IGNORECASE)
    match_date = re.search(r"(\d{2}/\d{2}/\d{4})", text)

    if match_id:
        label = match_id.group(1).replace(" ", "").upper()
    if match_date:
        date = match_date.group(1)

    return label, date


def classify_treatment(parcel: str) -> str:
    parcel_upper = parcel.upper()
    if "LIMPO" in parcel_upper:
        return "LIMPO"
    if "PEDRA" in parcel_upper:
        return "PEDRA"
    if "CELULA" in parcel_upper or "CÉLULA" in parcel_upper:
        return "CELULA"
    if "COMPOSTO" in parcel_upper:
        return "COMPOSTO"
    if "GRID" in parcel_upper:
        return "GRID"
    return "OUTRO"


def extract_parcel_code(parcel: str) -> str | None:
    match = re.search(r"(\d+\.\d+)", parcel)
    return match.group(1) if match else None


def main() -> None:
    raw = pd.read_excel(INPUT, header=None, sheet_name=0)

    header_row = 1
    first_data_row = 2
    first_weight_col = 1
    weight_cols = list(range(first_weight_col, raw.shape[1], 2))

    collection_meta: list[tuple[int, str, str | None]] = []
    for sequence, col in enumerate(weight_cols, start=1):
        label, date = parse_collection_label(raw.iat[header_row, col], sequence)
        collection_meta.append((col, label, date))

    records: list[dict[str, object]] = []
    for row in range(first_data_row, raw.shape[0]):
        parcel_value = raw.iat[row, 0]
        if pd.isna(parcel_value):
            continue

        parcel = str(parcel_value).strip()
        treatment = classify_treatment(parcel)
        if treatment not in {"LIMPO", "PEDRA"}:
            continue

        parcel_number_match = re.match(r"\s*(\d+)", parcel)
        parcel_number = int(parcel_number_match.group(1)) if parcel_number_match else None
        parcel_code = extract_parcel_code(parcel)

        for sequence, (col, collection, date_text) in enumerate(collection_meta, start=1):
            sediment_g = parse_number(raw.iat[row, col])
            if sediment_g is None:
                continue

            records.append(
                {
                    "tratamento": treatment,
                    "parcela": parcel,
                    "numero_parcela": parcel_number,
                    "codigo_parcela": parcel_code,
                    "coleta_seq": sequence,
                    "coleta": collection,
                    "data": date_text,
                    "sedimento_g": sediment_g,
                    "observacao_celula_original": str(raw.iat[row, col]).strip(),
                }
            )

    long_df = pd.DataFrame.from_records(records)
    if long_df.empty:
        raise RuntimeError("Nenhum dado LIMPO ou PEDRA foi extraido da planilha.")

    long_df["data"] = pd.to_datetime(long_df["data"], dayfirst=True, errors="coerce")
    long_df = long_df.sort_values(["tratamento", "numero_parcela", "coleta_seq"]).reset_index(drop=True)

    summary_parcel = (
        long_df.groupby(["tratamento", "parcela", "numero_parcela", "codigo_parcela"], dropna=False)
        .agg(
            n_coletas=("sedimento_g", "size"),
            sedimento_total_g=("sedimento_g", "sum"),
            sedimento_medio_g=("sedimento_g", "mean"),
            sedimento_mediano_g=("sedimento_g", "median"),
            sedimento_max_g=("sedimento_g", "max"),
            primeira_data=("data", "min"),
            ultima_data=("data", "max"),
        )
        .reset_index()
        .sort_values(["tratamento", "numero_parcela"])
    )

    summary_treatment = (
        summary_parcel.groupby("tratamento", dropna=False)
        .agg(
            n_parcelas=("parcela", "nunique"),
            n_coletas=("n_coletas", "sum"),
            sedimento_total_g=("sedimento_total_g", "sum"),
            sedimento_medio_por_parcela_g=("sedimento_total_g", "mean"),
            sedimento_mediano_por_parcela_g=("sedimento_total_g", "median"),
            sedimento_max_parcela_g=("sedimento_total_g", "max"),
        )
        .reset_index()
    )

    matrix = (
        long_df.pivot_table(
            index=["tratamento", "parcela", "numero_parcela", "codigo_parcela"],
            columns="coleta",
            values="sedimento_g",
            aggfunc="first",
        )
        .reset_index()
    )
    matrix.columns.name = None

    OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl", date_format="YYYY-MM-DD") as writer:
        long_df.to_excel(writer, sheet_name="dados_longos", index=False)
        summary_parcel.to_excel(writer, sheet_name="resumo_parcela", index=False)
        summary_treatment.to_excel(writer, sheet_name="resumo_tratamento", index=False)
        matrix.to_excel(writer, sheet_name="matriz_coletas", index=False)

    long_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"Arquivo Excel gerado: {OUTPUT_XLSX}")
    print(f"CSV gerado: {OUTPUT_CSV}")
    print("\nResumo por tratamento:")
    print(summary_treatment.to_string(index=False))
    print("\nResumo por parcela:")
    print(summary_parcel[["tratamento", "parcela", "n_coletas", "sedimento_total_g", "sedimento_medio_g"]].to_string(index=False))


if __name__ == "__main__":
    main()