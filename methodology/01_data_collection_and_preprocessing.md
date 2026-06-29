# Data Collection and Preprocessing

This document summarizes the data preparation workflow used to build the keyword co-occurrence networks for the longitudinal review of person re-identification (person Re-ID) research from 2015 to 2024.

## Bibliometric Corpus

The study focuses on person Re-ID publications indexed in the Web of Science Core Collection. The corpus was organized by publication year and then divided into time windows for longitudinal analysis.

Two temporal strategies were used:

- Cross-sectional windows: 2015-2016, 2017-2018, 2019-2020, 2021-2022, and 2023-2024.
- Cumulative windows: 2015-2016, 2015-2018, 2015-2020, 2015-2022, and 2015-2024.

The cross-sectional windows capture the most significant keywords within each two-year period. The cumulative windows capture the progressive consolidation of keywords from 2015 up to the endpoint year of each window.

## Keyword Extraction

Keyword co-occurrence networks were generated using the Sci2 Tool. In Sci2, keyword co-occurrence networks are constructed word by word. Multi-word expressions are therefore decomposed into individual terms before graph construction.

For example, the expression `metric learning` is represented by two nodes:

- `metric`
- `learn`

The second term is derived from `learning` through stemming.

## Text Normalization

The preprocessing workflow follows the normalization steps used by Sci2 before constructing the co-occurrence graph:

1. Convert text to lowercase.
2. Remove stop words using Lucene's `StandardAnalyzer`.
3. Apply Snowball/Porter2 stemming.
4. Build the keyword co-occurrence graph from the normalized terms.

As a result, graph labels often appear as stemmed terms rather than full words. For example:

- `learning` becomes `learn`
- `convolutional` becomes `convolut`
- `representation` becomes `represent`
- `surveillance` becomes `surveil`

## Interpretation of Stemmed Terms

Because Sci2 applies stemming, the keywords displayed in the graphs should be interpreted as normalized lexical roots rather than final publication-ready terms. Topics are identified by grouping words that belong to the same fine-grained or coarse-grained community, or by examining words connected by strong co-occurrence edges.

For example, the terms `metric` and `learn` should be interpreted together as the topic of metric learning. Similarly, `deep`, `neural`, `convolut`, and `network` should be interpreted as a group related to deep convolutional neural networks.

## Outputs

The preprocessing stage produces normalized keyword data that are used to construct weighted co-occurrence networks. These networks are then pruned, analyzed for communities, and visualized using consistent visual encodings across time periods.
