"""CRUD operations for the warehouse app."""

from json import dumps
from logging import getLogger
from typing import TYPE_CHECKING, Literal, overload

from database import GeneralItemModelType
from exceptions import (
    InvalidFieldsError,
    ItemExistsError,
    ItemNotFoundError,
    ItemSchemaNotFoundError,
    WarehouseNotFoundError,
)
from models import ItemPage, Warehouse, WarehousePage
from schemas import ItemBase, ItemResponse, ItemSchema, QueryParamType, WarehouseCreate
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Query, Session
from wg_utilities.loggers import add_stream_handler

if TYPE_CHECKING:
    from pydantic.main import IncEx

else:
    IncEx = set[str]


LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)


# Warehouse Operations


def create_warehouse(db: Session, /, warehouse: WarehouseCreate) -> Warehouse:
    """Create a warehouse."""
    db_warehouse = Warehouse(**warehouse.model_dump(exclude_unset=True, by_alias=True))

    db_warehouse.intialise_warehouse()

    try:
        db.add(db_warehouse)
        db.commit()
        db.refresh(db_warehouse)
    except OperationalError:
        # TODO improve this to only drop if the row doesn't exist
        db_warehouse.drop_warehouse(no_exist_ok=True)

    return db_warehouse


def delete_warehouse(db: Session, /, warehouse_name: str) -> None:
    """Delete a warehouse."""
    warehouse = get_warehouse(db, warehouse_name)

    warehouse.drop(no_exist_ok=True)

    db.query(Warehouse).filter(Warehouse.name == warehouse_name).delete()

    db.commit()


@overload
def get_warehouse(
    db: Session, /, name: str, *, no_exist_ok: Literal[False] = False
) -> Warehouse:
    ...


@overload
def get_warehouse(
    db: Session, /, name: str, *, no_exist_ok: Literal[True] = True
) -> Warehouse | None:
    ...


def get_warehouse(
    db: Session, /, name: str, *, no_exist_ok: bool = False
) -> Warehouse | None:
    """Get a warehouse by its name."""

    if (
        warehouse := db.query(Warehouse).filter(Warehouse.name == name).first()
    ) is None:
        if no_exist_ok:
            return None
        raise WarehouseNotFoundError(name)

    return warehouse


def get_warehouses(
    db: Session,
    /,
    *,
    offset: int = 0,
    limit: int | None = None,
    allow_no_warehouse_table: bool = False,
) -> WarehousePage:
    """Get a list of warehouses.

    Args:
        db (Session): The database session to use.
        offset (int, optional): The offset to use when querying the database.
            Defaults to 0.
        limit (int, optional): The limit to use when querying the database.
            Defaults to 100.
        allow_no_warehouse_table (bool, optional): Whether to suppress the error
            thrown because there is no `warehouse` table. Defaults to False.

    Returns:
        list[Warehouse]: A list of warehouses.
    """

    try:
        query = db.query(Warehouse).offset(offset)

        if limit is not None:
            query = query.limit(limit)

        warehouses = query.all()
        total = db.query(Warehouse).count()
    except OperationalError as exc:
        if (
            allow_no_warehouse_table
            and f"no such table: {Warehouse.__tablename__}" in str(exc)
        ):
            return WarehousePage.empty()

        raise

    limit = limit or total
    next_offset = offset + limit

    return WarehousePage(
        count=len(warehouses),
        warehouses=warehouses,
        next_offset=next_offset if next_offset < total else None,
        total=total,
    )


def update_warehouse(
    db: Session,
    /,
    warehouse_name: str,
    warehouse: WarehouseCreate,
) -> Warehouse:
    """Update a warehouse."""

    _ = db, warehouse_name, warehouse

    raise NotImplementedError(  # noqa: TRY003
        "Updating warehouses is not yet implemented."
    )


# Item Schema Operations


@overload
def get_item_schema(
    db: Session, /, item_name: str, *, no_exist_ok: Literal[False] = False
) -> ItemSchema:
    ...


@overload
def get_item_schema(
    db: Session, /, item_name: str, *, no_exist_ok: Literal[True] = True
) -> ItemSchema | None:
    ...


def get_item_schema(
    db: Session, /, item_name: str, *, no_exist_ok: bool = False
) -> ItemSchema | None:
    """Get an item's schema."""

    if (
        results := db.query(Warehouse.item_schema)
        .filter(Warehouse.item_name == item_name)
        .first()
    ) is None:
        if no_exist_ok:
            return None

        raise ItemSchemaNotFoundError(item_name)

    return results[0]


def get_item_schemas(db: Session, /) -> dict[str, ItemSchema]:
    """Get a list of items and their schemas."""
    return dict(db.query(Warehouse.item_name, Warehouse.item_schema))


# Item Operations


def create_item(
    db: Session, warehouse_name: str, item: GeneralItemModelType
) -> ItemResponse:
    """Create an item in a warehouse."""

    warehouse = get_warehouse(db, warehouse_name)

    pk_values = {pk_name: item[pk_name] for pk_name in warehouse.pk_name}

    if get_item_by_pk(db, warehouse_name, pk_values=pk_values, no_exist_ok=True):
        raise ItemExistsError(pk_values, warehouse_name)

    LOGGER.debug("Validating item into schema: %r ", item)

    item_schema: ItemBase = warehouse.item_schema_class.model_validate(item)

    LOGGER.debug("Dumping item into model: %r", item_schema)

    # Excluding unset values mean any default functions don't get returned as-is.
    db_item = warehouse.item_model(**item_schema.model_dump(exclude_unset=True))

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Re-parse so that we've got any new/updated values from the database.
    return warehouse.item_schema_class.model_validate(
        db_item.as_dict()
    )  # type: ignore[return-value]


def delete_item(
    db: Session, /, warehouse_name: str, search_values: QueryParamType
) -> None:
    """Delete an item from a warehouse."""

    warehouse = get_warehouse(db, warehouse_name)

    _ = get_item_by_pk(db, warehouse_name, pk_values=search_values)

    db.query(warehouse.item_model).filter(
        warehouse.item_model.pk == warehouse.parse_pk_dict(search_values)
    ).delete()
    db.commit()


@overload
def get_item_by_pk(
    db: Session,
    /,
    warehouse_name: str,
    pk_values: GeneralItemModelType | QueryParamType,
    field_names: list[str] | None = None,
    *,
    no_exist_ok: Literal[False] = False,
) -> GeneralItemModelType:
    ...


@overload
def get_item_by_pk(
    db: Session,
    /,
    warehouse_name: str,
    pk_values: GeneralItemModelType | QueryParamType,
    field_names: list[str] | None = None,
    *,
    no_exist_ok: Literal[True] = True,
) -> GeneralItemModelType | None:
    ...


def get_item_by_pk(
    db: Session,
    /,
    warehouse_name: str,
    pk_values: GeneralItemModelType | QueryParamType,
    field_names: list[str] | None = None,
    *,
    no_exist_ok: bool = False,
) -> GeneralItemModelType | None:
    """Get an item from a warehouse.

    Args:
        db (Session): The database session to use.
        warehouse_name (str): The name of the warehouse to get the item from.
        pk_values (dict[str, str]): The primary key values of the item to get.
        field_names (list[str], optional): The names of the fields to return. Defaults
            to None.
        no_exist_ok (bool, optional): Whether to suppress the error thrown if the item
            doesn't exist. Defaults to False.

    Returns:
        ItemResponse | None: The item, or None if it doesn't exist.
    """

    warehouse = get_warehouse(db, warehouse_name)

    if field_names and (
        unknown_fields := [
            field_name
            for field_name in field_names
            if field_name not in warehouse.item_model.__table__.columns
        ]
    ):
        raise InvalidFieldsError(unknown_fields)

    item_pk = warehouse.parse_pk_dict(pk_values)

    if (item := db.query(warehouse.item_model).get(item_pk)) is None:
        if no_exist_ok:
            return None

        raise ItemNotFoundError(item_pk, warehouse_name)

    return item.as_dict(include=field_names)


def get_items(
    db: Session,
    /,
    warehouse_name: str,
    field_names: list[str] | None = None,
    *,
    search_params: QueryParamType,
    offset: int = 0,
    limit: int = 100,
) -> ItemPage | GeneralItemModelType:
    # pylint: disable=too-many-locals
    """Get a list of items in a warehouse.

    Args:
        db (Session): The database session to use.
        warehouse_name (str): The name of the warehouse to get the items from.
        field_names (list[str], optional): The names of the fields to return. Defaults
            to None.
        search_params (dict[str, str], optional): The parameters to search for. Defaults
            to None.
        offset (int, optional): The offset to use when querying the database.
            Defaults to 0.
        limit (int, optional): The limit to use when querying the database. Defaults
            to 100.

    Returns:
        list[dict[str, object]]: A list of items in the warehouse.

    Raises:
        _HTTPException: Raised if an invalid field name is provided.
    """

    warehouse = get_warehouse(db, warehouse_name)

    if warehouse.search_params_are_pks(search_params):
        LOGGER.debug("Searching for item by primary key.")
        return get_item_by_pk(
            db,
            warehouse_name=warehouse_name,
            field_names=field_names,
            pk_values=search_params,
        )

    if not field_names:
        query: Query[Warehouse] = db.query(warehouse.item_model)
    else:
        field_names = sorted(field_names)

        try:
            fields = tuple(
                getattr(warehouse.item_model, field_name) for field_name in field_names
            )
        except AttributeError as exc:
            raise InvalidFieldsError(exc.name) from exc

        query = db.query(*fields)

    if search_params:
        for k, v in search_params.items():
            query = query.filter(getattr(warehouse.item_model, k) == v)

    results = query.offset(offset).limit(limit).all()

    if field_names:
        items: list[GeneralItemModelType] = [
            dict(zip(field_names, row, strict=True)) for row in results
        ]
    else:
        items = [row.as_dict() for row in results]

    total = get_item_count(db, warehouse_name)

    next_offset = offset + limit

    return ItemPage(
        count=len(items),
        items=items,
        next_offset=next_offset if next_offset < total else None,
        total=total,
    )


def update_item(
    db: Session,
    /,
    *,
    warehouse_name: str,
    pk_values: GeneralItemModelType,
    item_update: GeneralItemModelType,
) -> GeneralItemModelType:
    """Update an item in a warehouse."""

    warehouse = get_warehouse(db, warehouse_name)

    current_item_dict = get_item_by_pk(db, warehouse_name, pk_values=pk_values)

    new_item_dict = current_item_dict | item_update

    LOGGER.debug(
        "Parsed item update into new item: %s",
        dumps(new_item_dict, indent=2, sort_keys=True),
    )

    warehouse.item_schema_class.model_validate(new_item_dict)
    item_pk = warehouse.parse_pk_dict(pk_values)

    try:
        db.query(warehouse.item_model).filter(
            warehouse.item_model.pk == item_pk
        ).update(item_update)
    except IntegrityError as exc:
        if "unique constraint failed" in str(exc).lower():
            raise ItemExistsError(pk_values, warehouse_name) from exc
        raise

    db.commit()
    return get_item_by_pk(db, warehouse_name, pk_values=pk_values)


# TODO caching!
def get_item_count(db: Session, /, warehouse_name: str) -> int:
    """Get the number of items in a warehouse."""

    warehouse = get_warehouse(db, warehouse_name)

    return db.query(warehouse.item_model).count()
