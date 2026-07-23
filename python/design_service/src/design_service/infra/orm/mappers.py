from python.libs.entities.design import ChatTheme, MapPinStyle
from python.design_service.src.design_service.infra.orm.models import ChatThemeModel, MapPinStyleModel


def pin_model_to_dto(m: MapPinStyleModel) -> MapPinStyle:
    return MapPinStyle(
        id=m.id,
        deleted=m.deleted,
        created_at=m.created_at,
        updated_at=m.updated_at,
        code=m.code,
        name=m.name,
        image_url=m.image_url,
        gif_url=m.gif_url,
        anchor_x=m.anchor_x,
        anchor_y=m.anchor_y,
    )


def theme_model_to_dto(m: ChatThemeModel) -> ChatTheme:
    return ChatTheme(
        id=m.id,
        deleted=m.deleted,
        created_at=m.created_at,
        updated_at=m.updated_at,
        code=m.code,
        name=m.name,
        background_url=m.background_url,
        font_family=m.font_family,
        colors=dict(m.colors or {}),
    )


def pin_to_api(p: MapPinStyle) -> dict:
    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "image_url": p.image_url,
        "gif_url": p.gif_url,
        "anchor_x": p.anchor_x,
        "anchor_y": p.anchor_y,
    }


def theme_to_api(t: ChatTheme) -> dict:
    return {
        "id": t.id,
        "code": t.code,
        "name": t.name,
        "background_url": t.background_url,
        "font_family": t.font_family,
        "colors": t.colors,
    }
