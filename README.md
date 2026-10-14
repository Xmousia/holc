# Reading the Redlining Record

Two studies of the Home Owners' Loan Corporation (HOLC) redlining record, plus two Virginia city maps.

Live site: https://xmousia.github.io/holc/

| Page | What it does |
|---|---|
| [`lexicon/`](lexicon/) | **The Appraisers' Lexicon.** Every word in 7,929 transcribed area descriptions, placed on the A-to-D grade scale, with full-text search and concordance lines. |
| [`audit/`](audit/) | **The Redlining Audit.** An economics-only model of the grades, a like-for-like comparison, a race-field flip test, and the areas where appraisers departed from their own numbers. |
| [`maps/newport-news/`](maps/newport-news/) | Newport News, VA (April 3, 1937): graded areas over the original georeferenced sheet. |
| [`maps/roanoke/`](maps/roanoke/) | Roanoke and Salem, VA (May 15, 1937): graded areas over the original sheets, with each area's transcribed form. |

The pages are static HTML. They load D3 from cdnjs and fonts from Google Fonts; everything else is in this repository.

## Reproducing the numbers

```sh
git clone https://github.com/americanpanorama/HOLC_Area_Description_Data
pip install -r analysis/requirements.txt
export HOLC_AD=HOLC_Area_Description_Data/ad_data.json
python analysis/build_lexicon.py   # writes lexicon/corpus.json and data/lexicon.json
python analysis/build_audit.py     # writes data/audit.json
```

- `analysis/parse.py` turns the forms' free-text fields (income, prices, age, repair, occupancy, owner-occupancy, the "Negro" field) into numbers.
- `analysis/build_audit.py` fits a multinomial logistic regression on the economic fields with five-fold cross-validation grouped by city, then runs the comparisons shown on the audit page.
- `analysis/build_scans.py` crops Mapping Inequality's georeferenced GeoTIFF scans to a city's extent.

The `lexicon/index.html` and `audit/index.html` pages embed `data/lexicon.json` and `data/audit.json` at the point marked in the page script; after rebuilding the data, replace the embedded object with the new file's contents.

Area polygons for the maps (`data/*-areas.json`) come from Mapping Inequality's national GeoJSON, joined to the form transcriptions by `area_id`.

## Limits

Free-text fields were parsed with rules, not by hand, and some values are misread. The race field is blank on many later forms. Small groups (for example, A- or B-like areas with Black residents recorded) give imprecise estimates. All findings describe HOLC's own records, not the neighborhoods themselves.

## Sources and license

Data: Robert K. Nelson, LaDale Winling, Richard Marciano, Nathan Connolly, et al., "Mapping Inequality," *American Panorama*, ed. Robert K. Nelson and Edward L. Ayers, https://dsl.richmond.edu/panorama/redlining/, and the [HOLC Area Description Data](https://github.com/americanpanorama/HOLC_Area_Description_Data). Mapping Inequality is licensed [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

See [LICENSE.md](LICENSE.md).
