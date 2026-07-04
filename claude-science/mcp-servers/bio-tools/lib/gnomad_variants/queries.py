"""GraphQL documents used by the modern tool.

Field selections are deliberately lean: the gnomAD API is complexity-limited,
and an agent consuming the output pays per token. Each document selects the
scientifically load-bearing fields only.
"""

VARIANT = """
query Variant($variantId: String!, $dataset: DatasetId!) {
  variant(variantId: $variantId, dataset: $dataset) {
    variant_id reference_genome chrom pos ref alt rsids
    exome { ac an af homozygote_count hemizygote_count filters }
    genome { ac an af homozygote_count hemizygote_count filters }
  }
}
"""

VARIANT_SEARCH = """
query VariantSearch($query: String!, $dataset: DatasetId!) {
  variant_search(query: $query, dataset: $dataset) { variant_id }
}
"""

GENE_LOOKUP_FIELDS = """
    gene_id symbol name canonical_transcript_id chrom start stop strand
"""

GENE_CONSTRAINT = """
query GeneConstraint($symbol: String, $geneId: String) {
  gene(gene_symbol: $symbol, gene_id: $geneId, reference_genome: GRCh38) {
    gene_id symbol canonical_transcript_id chrom start stop strand
    gnomad_constraint {
      exp_lof obs_lof oe_lof oe_lof_lower oe_lof_upper
      exp_mis obs_mis oe_mis oe_mis_lower oe_mis_upper
      exp_syn obs_syn oe_syn oe_syn_lower oe_syn_upper
      pli lof_z mis_z syn_z
    }
  }
}
"""

GENE_VARIANTS = """
query GeneVariants($symbol: String, $geneId: String, $dataset: DatasetId!) {
  gene(gene_symbol: $symbol, gene_id: $geneId, reference_genome: GRCh38) {
    gene_id symbol start stop chrom
    variants(dataset: $dataset) {
      variant_id pos ref alt rsids
      exome { ac an af } genome { ac an af }
    }
  }
}
"""

REGION_VARIANTS = """
query RegionVariants($chrom: String!, $start: Int!, $stop: Int!, $dataset: DatasetId!) {
  region(chrom: $chrom, start: $start, stop: $stop, reference_genome: GRCh38) {
    variants(dataset: $dataset) {
      variant_id pos ref alt rsids
      exome { ac an af } genome { ac an af }
    }
  }
}
"""

LIFTOVER = """
query Liftover($source: String!, $rg: ReferenceGenomeId!) {
  liftover(source_variant_id: $source, reference_genome: $rg) {
    source { variant_id reference_genome }
    liftover { variant_id reference_genome }
    datasets
  }
}
"""

CLINVAR_VARIANTS = """
query ClinvarVariants($symbol: String, $geneId: String) {
  meta { clinvar_release_date }
  gene(gene_symbol: $symbol, gene_id: $geneId, reference_genome: GRCh38) {
    gene_id symbol
    clinvar_variants {
      variant_id clinvar_variation_id clinical_significance gold_stars
      review_status major_consequence pos transcript_id
      in_gnomad
    }
  }
}
"""

STRUCTURAL_VARIANTS_GENE = """
query StructuralVariantsGene($symbol: String, $geneId: String, $dataset: StructuralVariantDatasetId!) {
  gene(gene_symbol: $symbol, gene_id: $geneId, reference_genome: GRCh38) {
    gene_id symbol
    structural_variants(dataset: $dataset) {
      variant_id consequence major_consequence ac an af homozygote_count
      hemizygote_count chrom pos end chrom2 pos2 type length filters
    }
  }
}
"""

STRUCTURAL_VARIANT = """
query StructuralVariant($variantId: String!, $dataset: StructuralVariantDatasetId!) {
  structural_variant(variantId: $variantId, dataset: $dataset) {
    variant_id chrom pos end chrom2 pos2 type length ac an af
    homozygote_count hemizygote_count filters qual
    consequences { consequence genes }
    algorithms evidence
  }
}
"""

MITOCHONDRIAL_VARIANTS_GENE = """
query MitochondrialVariantsGene($symbol: String, $geneId: String, $dataset: DatasetId!) {
  gene(gene_symbol: $symbol, gene_id: $geneId, reference_genome: GRCh38) {
    gene_id symbol
    mitochondrial_variants(dataset: $dataset) {
      variant_id pos ac_het ac_hom an max_heteroplasmy filters
    }
  }
}
"""

MITOCHONDRIAL_VARIANTS_REGION = """
query MitochondrialVariantsRegion($start: Int!, $stop: Int!, $dataset: DatasetId!) {
  region(chrom: "M", start: $start, stop: $stop, reference_genome: GRCh38) {
    mitochondrial_variants(dataset: $dataset) {
      variant_id pos ac_het ac_hom an max_heteroplasmy filters
    }
  }
}
"""
