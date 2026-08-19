# GPRbase API — Reference

The full API reference lives on the GPRbase site, where it is maintained
alongside the API itself:

**https://www.gprbase.com/api/**

It covers the endpoints, every field of the dataset object, application keys,
citations, error codes and usage notes. Available in English and French.

## In short

```
GET https://www.gprbase.com/api/datasets.json        full catalogue
GET https://www.gprbase.com/api/datasets/{id}.json   one dataset + citations
```

Read-only, no key, no registration, CORS open. Responses are cached for one
hour. The API returns metadata and page addresses, not download links: access to
the files goes through the request form on the site.

The clients in this repository wrap both endpoints and handle filtering,
multi-value fields and citation generation. See the [README](README.md).
