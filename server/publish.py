from ayon_server.settings import BaseSettingsModel, SettingsField


class BurninOptionsModel(BaseSettingsModel):
    enabled: bool = SettingsField(False, title="Enabled")
    font_size: int = SettingsField(24, title="Font Size", ge=1)
    font_color: str = SettingsField("white", title="Font Color")
    font_path: str = SettingsField("", title="Font Path (Optional)")
    top_left: str = SettingsField("{asset}", title="Top Left")
    top_center: str = SettingsField("{task}", title="Top Center")
    top_right: str = SettingsField("{version}", title="Top Right")
    bottom_left: str = SettingsField("{date}", title="Bottom Left")
    bottom_center: str = SettingsField("{time}", title="Bottom Center")
    bottom_right: str = SettingsField("Frame: {frame}", title="Bottom Right")


class ExtractReviewModel(BaseSettingsModel):
    burnin: BurninOptionsModel = SettingsField(
        default_factory=BurninOptionsModel,
        title="Burnin"
    )


class ExtractRedshiftRenderModel(BaseSettingsModel):
    burnin: BurninOptionsModel = SettingsField(
        default_factory=BurninOptionsModel,
        title="Burnin"
    )


class PublishPluginsModel(BaseSettingsModel):
    Cinema4DExtractReview: ExtractReviewModel = SettingsField(
        default_factory=ExtractReviewModel,
        title="Render Review"
    )
    ExtractRedshiftRender: ExtractRedshiftRenderModel = SettingsField(
        default_factory=ExtractRedshiftRenderModel,
        title="Render Redshift"
    )
