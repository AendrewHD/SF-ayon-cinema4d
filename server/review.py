from ayon_server.settings import BaseSettingsModel, SettingsField


class ExtractReviewSettingsModel(BaseSettingsModel):
    _isGroup = True
    keep_images: bool = SettingsField(
        False,
        title="Keep Review Images"
    )
    image_format: str = SettingsField(
        "PNG",
        title="Image format",
        enum_resolver=lambda: ["PNG", "JPEG"]
    )
    mov_format: str = SettingsField(
        "QuickTime",
        title="Movie format",
        enum_resolver=lambda: ["QuickTime", "AVI"]
    )
    use_for_all_render_families: bool = SettingsField(
        False,
        title="Use for all Render families"
    )


class ReviewPluginsModel(BaseSettingsModel):
    ExtractReview: ExtractReviewSettingsModel = SettingsField(
        default_factory=ExtractReviewSettingsModel,
        title="Extract Review"
    )


DEFAULT_CINEMA4D_REVIEW_SETTINGS = {
    "ExtractReview": {
        "keep_images": False,
        "image_format": "PNG",
        "mov_format": "QuickTime",
        "use_for_all_render_families": False
    }
}
