from arxiv.document.metadata import DocMetadata
from .scaffold import ArticleScaffoldMetadata

NO_LICENSE = "No License"

def scaffold_metadata_from_published(abs_meta : DocMetadata) -> ArticleScaffoldMetadata:
    short_label = abs_meta.license and abs_meta.license.get_short_label()
    license_str = (
        f"License: {short_label}"
        if short_label and short_label != NO_LICENSE
        else NO_LICENSE
    )
    date_of_version = abs_meta.get_datetime_of_version(abs_meta.version)
    date_of_version_str = date_of_version.strftime("%d %b %Y") if date_of_version else ''
    primary_category_str = str(abs_meta.primary_category.id) if abs_meta.primary_category else ''
    
    return ArticleScaffoldMetadata(
        license=license_str,
        page_id=abs_meta.arxiv_id_v,
        primary_category=primary_category_str,
        date_of_version=date_of_version_str,
        published=True
    )

