"""Run the pinned bench battery (bench/battery.json) through GtexExpression.

Shared by bench/run_gate.py (accuracy gate), bench/freeze_battery.py
(reference capture) and bench/run_bench.py (cost measurement) so all three
exercise the identical code path.
"""
from __future__ import annotations

from .tool import GtexExpression


def run_battery(tool: GtexExpression, battery: dict) -> dict:
    """Execute every battery query; returns a dict keyed by battery section."""
    b = battery
    out: dict = {"dataset_id": tool.dataset_id}

    out["tissue_sites"] = tool.tissue_sites()
    out["dataset_info"] = tool.dataset_info()
    out["resolve_genes"] = tool.resolve_genes(b["panel_symbols"])
    out["median_expression"] = tool.median_expression(
        b["panel_gencode_ids"], b["median_tissues"])
    out["expression_summary"] = tool.expression_summary(b["summary_gene"])
    out["gene_expression"] = tool.gene_expression(
        b["sample_level"]["gencode_id"], [b["sample_level"]["tissue"]])
    out["top_expressed"] = tool.top_expressed(
        b["top_expressed"]["tissue"], n=b["top_expressed"]["n"],
        filter_mt_gene=b["top_expressed"]["filter_mt_gene"])
    out["eqtl_genes"] = tool.eqtl_genes(b["egene_tissue"])
    out["single_tissue_eqtls"] = tool.single_tissue_eqtls(
        gencode_id=b["single_tissue_eqtl"]["gencode_id"],
        tissue_site_detail_id=b["single_tissue_eqtl"]["tissue"])
    out["multi_tissue_eqtls"] = tool.multi_tissue_eqtls(
        b["multi_tissue_eqtl"]["gencode_id"],
        variant_id=b["multi_tissue_eqtl"]["variant_id"])
    out["calculate_eqtl"] = tool.calculate_eqtl(
        b["dyn_eqtl"]["gencode_id"], b["dyn_eqtl"]["variant_id"],
        b["dyn_eqtl"]["tissue"])
    out["sample_info"] = [
        tool.sample_info(**{k: v for k, v in spec.items() if k != "label"})
        for spec in b["sample_queries"]]
    return out
