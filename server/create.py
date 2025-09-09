from ayon_server.settings import BaseSettingsModel, SettingsField


#Creator Plugins
class CreatorModel(BaseSettingsModel):
    enabled: bool = SettingsField(title="Enabled")
    default_variants: list[str] = SettingsField(
        title="Default Products",
        default_factory=list,
    )
    
def review_render_types_enum():
    return [
        {"label": "Viewport", "value": "viewport"},
        {"label": "Redshift", "value": "redshift"},
        {"label": "Arnold", "value": "arnold"},
        {"label": "Octane", "value": "octane"}
    ]
    
class CreateReviewModel(BaseSettingsModel):
    enabled: bool = SettingsField(title="Enabled")
    default_variants: list[str] = SettingsField(
        title="Default Products",
        default_factory=list,
    )
    render_type: str = SettingsField(
        title="Default Render Engine",
        enum_resolver=review_render_types_enum,
    )
    
class CreatePluginsModel(BaseSettingsModel):
    CreateReview: CreateReviewModel = SettingsField(
        title="Create Review"
    )

DEFAULT_CINEMA4D_CREATE_SETTINGS = {
    "CreateReview": {
        "enabled": True,
        "default_variants": ["Main"],
        "render_type": "viewport"
    }
}