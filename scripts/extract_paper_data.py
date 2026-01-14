#!/usr/bin/env python3
"""
Paper Data Extraction Tool
Extracts text from PDFs and provides extraction templates
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Try to import PDF libraries
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    print("Note: PyPDF2 not installed. Install with: pip install PyPDF2")


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF"""
    if not HAS_PYPDF2:
        return None
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None


def create_extraction_template(paper_id: str, title: str, parameters: List[str]) -> str:
    """Create extraction template for a paper"""
    
    template = f"""# Extraction Template: {paper_id}

**Paper:** {title}
**Date Extracted:** 2026-01-14
**Extractor:** [Your name]

---

## Parameters to Extract

"""
    
    for param in parameters:
        template += f"""### {param}

**What to extract:**
- Mean/median values
- Standard deviations
- Sample sizes (n)
- Effect sizes (Cohen's d, Hedges' g, etc.)
- Confidence intervals
- p-values
- Group comparisons (if applicable)

**Location in paper:**
- [ ] Abstract
- [ ] Methods section
- [ ] Results section
- [ ] Tables (which table: ______)
- [ ] Figures (which figure: ______)

**Extracted Values:**
```
Control/Typical Group:
  Mean (SD): _____
  N: _____
  
Clinical/ASD/ADHD Group:
  Mean (SD): _____
  N: _____
  
Effect Size:
  Type: [Cohen's d / Hedges' g / other]
  Value: _____
  95% CI: [_____, _____]
  
Statistical Test:
  Test type: _____
  Statistic: _____
  p-value: _____
```

**Direct Quote (with page number):**
> "..." (p. ___)

**Notes/Caveats:**
- 

---

"""
    
    template += """## Quality Assessment

- [ ] Sample size adequate (n > 20 per group)
- [ ] Control group included
- [ ] Effect size reported or calculable
- [ ] Replication of prior findings
- [ ] Clear measurement methodology

## Confidence Rating

After extraction, rate confidence:
- [ ] HIGH - Direct measurement, large sample, clear methodology
- [ ] MODERATE - Indirect measure, adequate sample, some ambiguity
- [ ] LOW - Small sample, unclear methods, high variability

## Update Required

Based on extraction:
- [ ] Current parameter value is CORRECT
- [ ] Current parameter value needs ADJUSTMENT to: _____
- [ ] Parameter needs RECALCULATION using: _____

---

## Conversion to Simulation Units

**Parameter:** {parameters[0] if parameters else "____"}
**Current Value:** _____
**Literature Value:** _____
**Scale/Units:** _____

**Conversion Formula:**
```
simulation_value = literature_value * conversion_factor
where conversion_factor = _____
```

**Justification for conversion:**


**New Recommended Value:** _____

"""
    
    return template


def main():
    print("=" * 70)
    print("PAPER DATA EXTRACTION TOOL")
    print("=" * 70)
    
    papers_dir = Path("papers")
    extractions_dir = Path("extractions")
    extractions_dir.mkdir(exist_ok=True)
    
    # Define papers and what to extract
    extraction_specs = {
        "corbett2009": {
            "title": "Elevated cortisol during play in children with autism",
            "pdf": "corbett2009.pdf",
            "parameters": [
                "asd_stress_baseline",
                "asd_stress_reactivity",
                "asd_stress_recovery_rate"
            ],
            "key_data": """
KEY DATA TO EXTRACT:

1. Baseline Cortisol Levels
   - ASD group mean cortisol (μg/dL or nmol/L)
   - NT (neurotypical) control mean cortisol
   - Time of measurement
   
2. Cortisol During Social Interaction
   - Peak cortisol during play
   - Change from baseline
   
3. Recovery Pattern
   - Cortisol at recovery timepoints
   - Time to return to baseline
   
4. Effect Sizes
   - ASD vs NT differences
   - Cohen's d or Hedges' g

LOOK FOR:
- Table with cortisol values by group and timepoint
- Figure showing cortisol trajectories
- Results section with statistical comparisons
            """
        },
        "huang-pollock2012": {
            "title": "Evaluating vigilance deficits in ADHD",
            "pdf": "huang-pollock2012.pdf",
            "parameters": [
                "adhd_attention_stability",
                "adhd_vigilance_decrement",
                "adhd_response_variability"
            ],
            "key_data": """
KEY DATA TO EXTRACT:

1. Vigilance Decrement
   - Performance decline over time (slope)
   - RT increase per minute/block
   - Accuracy decline per minute/block
   
2. Overall Performance
   - Mean RT (ADHD vs control)
   - RT variability (SD or coefficient of variation)
   - Error rates (omission, commission)
   
3. Effect Sizes
   - Meta-analytic d for vigilance deficit
   - Meta-analytic d for RT variability
   
4. Sample Characteristics
   - Total N across studies
   - Age ranges
   - Task types (CPT, sustained attention)

LOOK FOR:
- Meta-analysis summary statistics table
- Forest plots with effect sizes
- Vigilance slope analyses
- Heterogeneity statistics
            """
        }
    }
    
    # Create extraction templates
    for paper_id, spec in extraction_specs.items():
        pdf_path = papers_dir / spec['pdf']
        
        if not pdf_path.exists():
            print(f"\n❌ {paper_id}: PDF not found at {pdf_path}")
            continue
        
        print(f"\n📄 Processing: {paper_id}")
        print(f"   Title: {spec['title']}")
        print(f"   PDF: {pdf_path} ({pdf_path.stat().st_size / 1024:.1f} KB)")
        
        # Create template
        template_path = extractions_dir / f"{paper_id}_extraction.md"
        template = create_extraction_template(
            paper_id,
            spec['title'],
            spec['parameters']
        )
        
        # Add key data section
        template = template.replace(
            "## Parameters to Extract",
            f"{spec['key_data']}\n\n---\n\n## Parameters to Extract"
        )
        
        with open(template_path, 'w') as f:
            f.write(template)
        
        print(f"   ✓ Created extraction template: {template_path}")
        
        # Try to extract text
        if HAS_PYPDF2:
            print(f"   Extracting text...")
            text = extract_text_from_pdf(pdf_path)
            
            if text:
                text_path = extractions_dir / f"{paper_id}_fulltext.txt"
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"   ✓ Extracted text: {text_path} ({len(text)} chars)")
                
                # Search for key terms
                key_terms = ['cortisol', 'mean', 'SD', 'effect size', 
                            'vigilance', 'ADHD', 'autism', 'p <', 'd =']
                found_terms = [term for term in key_terms if term.lower() in text.lower()]
                
                if found_terms:
                    print(f"   ✓ Found key terms: {', '.join(found_terms[:5])}")
            else:
                print(f"   ⚠ Could not extract text from PDF")
        else:
            print(f"   ⚠ PyPDF2 not available - manual extraction only")
    
    # Create master extraction summary
    print(f"\n{'=' * 70}")
    print("EXTRACTION TEMPLATES CREATED")
    print(f"{'=' * 70}")
    print(f"\nLocation: {extractions_dir}/")
    print(f"\nNext steps:")
    print(f"1. Open each *_extraction.md file")
    print(f"2. Read the corresponding PDF")
    print(f"3. Fill in the extraction template")
    print(f"4. Run the update script to apply changes")
    
    print(f"\nFiles created:")
    for f in sorted(extractions_dir.glob("*")):
        print(f"  - {f.name}")
    
    # Create quick reference guide
    guide_path = extractions_dir / "EXTRACTION_GUIDE.md"
    with open(guide_path, 'w') as f:
        f.write("""# Extraction Guide

## How to Extract Data

### Step 1: Open the PDF
- Use preview/Acrobat to open the PDF
- Have the extraction template open alongside

### Step 2: Locate Key Information

**For Cortisol/Stress Papers (corbett2009):**
1. Find the Methods section - note measurement details
2. Look for Results tables with cortisol values
3. Find figures showing cortisol trajectories
4. Extract: Mean, SD, N for each group and timepoint
5. Note statistical tests and p-values

**For Meta-Analysis Papers (huang-pollock2012):**
1. Find the meta-analysis summary table
2. Look for forest plots with effect sizes
3. Extract: Overall effect size (d or g), 95% CI, N studies
4. Note heterogeneity statistics (I², Q)
5. Look for moderator analyses

### Step 3: Fill in Template
- Copy exact values from paper
- Include page numbers
- Quote key sentences
- Note any caveats or limitations

### Step 4: Quality Check
- Verify sample sizes are reasonable
- Check if control group is comparable
- Ensure units are clear
- Confirm calculations if doing conversions

### Step 5: Recommend Updates
- Compare extracted value to current parameter
- Calculate conversion if needed (see SCALE_MAPPINGS.md)
- Recommend new value with justification

## Common Pitfalls

❌ **Wrong units:** Cortisol can be in μg/dL, nmol/L, or ng/mL
❌ **Missing context:** Always note baseline, condition, timepoint
❌ **Pooling inappropriately:** Don't average across incompatible conditions
❌ **Ignoring moderators:** Age, medication status matter

## Example Extraction

```markdown
### asd_stress_baseline

**Extracted Values:**
Control/Typical Group:
  Mean (SD): 0.45 (0.18) μg/dL
  N: 28
  
ASD Group:
  Mean (SD): 0.68 (0.24) μg/dL
  N: 38
  
Effect Size:
  Type: Cohen's d
  Value: 1.08
  95% CI: [0.54, 1.62]
  
Statistical Test:
  Test type: Independent t-test
  Statistic: t(64) = 3.89
  p-value: p < .001

**Direct Quote:**
> "Children with ASD showed significantly elevated cortisol 
> at baseline (M = 0.68, SD = 0.24) compared to typically 
> developing children (M = 0.45, SD = 0.18), t(64) = 3.89, 
> p < .001, d = 1.08" (p. 8)

**Notes:**
- Measured in morning (9-11am)
- Children ages 8-12
- ASD diagnosis confirmed by ADOS
- Saliva samples, assayed by ELISA
```

## Converting to Simulation Units

See `docs/SCALE_MAPPINGS.md` for conversion formulas.

Example:
```python
# Cortisol literature value: 0.68 μg/dL (ASD)
# Baseline for NT: 0.45 μg/dL
# Simulation needs stress level (0-1 scale)

# Convert to relative elevation
elevation_ratio = 0.68 / 0.45  # = 1.51 (51% higher)

# Map to stress scale (0-1, where 0.5 = typical baseline)
asd_stress_baseline = 0.5 * elevation_ratio  # = 0.76

# Round to 2 decimals
asd_stress_baseline = 0.76
```

## After Extraction

1. Save completed extraction file
2. Update `docs/EVIDENCE_TABLE.md` with status ✅
3. Update `src/rpm_ee/clinical/presets.py` if values change
4. Document changes in git commit
5. Run tests to ensure no breaking changes
""")
    
    print(f"\n✓ Created extraction guide: {guide_path}")
    print(f"\n{'=' * 70}")
    print("Ready for manual extraction!")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
