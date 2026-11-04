-- Historical article URLs for the study outlets, from GDELT's Global Knowledge Graph.
-- Run in the BigQuery sandbox (free tier, no credit card). The partition filter keeps
-- the scan small; run one year at a time and export the result as gdelt_urls.csv.
-- Then:  python -m influence.news.crawl urls --file gdelt_urls.csv --max 5000

SELECT DISTINCT
  DocumentIdentifier AS url,
  SourceCommonName   AS outlet,
  PARSE_TIMESTAMP('%Y%m%d%H%M%S', CAST(DATE AS STRING)) AS seen_at
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE _PARTITIONTIME BETWEEN TIMESTAMP('2024-01-01') AND TIMESTAMP('2024-12-31')
  AND SourceCommonName IN (
    'okezone.com','inews.id','sindonews.com','metrotvnews.com','mediaindonesia.com',
    'viva.co.id','tvonenews.com','beritasatu.com',
    'kompas.com','tempo.co','detik.com','cnnindonesia.com','kumparan.com','idntimes.com')
  -- keep the crawl focused: articles GDELT tagged with our topics or names
  AND (
    REGEXP_CONTAINS(LOWER(V2Themes), r'econ_bank|agricult|deforest|env_forest|palm')
    OR REGEXP_CONTAINS(LOWER(AllNames), r'paloh|tanoesoedibjo|bakrie|danantara|wilmar|sinar mas|salim|bank rakyat|bank negara|bank tabungan|bank mandiri')
  );
