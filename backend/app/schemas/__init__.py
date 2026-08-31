"""Marshmallow schemas cho dữ liệu đầu vào API.

Schema chịu trách nhiệm kiểm tra hình dạng và kiểu dữ liệu. Các quy tắc nghiệp vụ
(phạm vi đơn vị, mã trùng, sức chứa chức vụ...) tiếp tục nằm trong service.
"""
from __future__ import annotations

from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from ..models.enums import (
    ASSIGNMENT_TYPES,
    EMPLOYEE_STATUSES,
    EMPLOYMENT_TYPES,
    GENDERS,
    UNIT_TYPES,
)


class ApiSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    nullable_fields: set[str] = set()

    @pre_load
    def empty_strings_to_none(self, data, **_kwargs):
        if not isinstance(data, dict):
            return data
        result = dict(data)
        for name in self.nullable_fields:
            if result.get(name) == "":
                result[name] = None
        return result


required = {"required": "Trường này là bắt buộc."}


class LoginSchema(ApiSchema):
    username = fields.String(required=True, validate=validate.Length(min=1), error_messages=required)
    password = fields.String(required=True, validate=validate.Length(min=1), error_messages=required)


class ChangePasswordSchema(ApiSchema):
    old_password = fields.String(required=True, error_messages=required)
    new_password = fields.String(required=True, validate=validate.Length(min=8), error_messages=required)


class EmployeeBaseSchema(ApiSchema):
    nullable_fields = {
        "date_of_birth", "gender", "identity_number", "phone", "email", "address",
        "professional_title", "employment_type", "recruitment_date", "avatar_url", "notes",
    }

    employee_code = fields.String()
    full_name = fields.String()
    date_of_birth = fields.Date(allow_none=True)
    gender = fields.String(allow_none=True, validate=validate.OneOf(sorted(GENDERS)))
    identity_number = fields.String(allow_none=True)
    phone = fields.String(allow_none=True)
    email = fields.Email(allow_none=True)
    address = fields.String(allow_none=True)
    professional_title = fields.String(allow_none=True)
    employment_type = fields.String(
        allow_none=True, validate=validate.OneOf(sorted(EMPLOYMENT_TYPES))
    )
    recruitment_date = fields.Date(allow_none=True)
    status = fields.String(validate=validate.OneOf(sorted(EMPLOYEE_STATUSES)))
    avatar_url = fields.String(allow_none=True)
    notes = fields.String(allow_none=True)


class EmployeeCreateSchema(EmployeeBaseSchema):
    employee_code = fields.String(required=True, error_messages=required)
    full_name = fields.String(required=True, error_messages=required)
    unit_id = fields.Integer(required=True, strict=True, error_messages=required)
    position_id = fields.Integer(required=True, strict=True, error_messages=required)
    start_date = fields.Date(allow_none=True)
    decision_number = fields.String(allow_none=True)
    decision_date = fields.Date(allow_none=True)
    note = fields.String(allow_none=True)
    replace_existing = fields.Boolean(load_default=False)

    nullable_fields = EmployeeBaseSchema.nullable_fields | {
        "start_date", "decision_number", "decision_date", "note"
    }


class EmployeeUpdateSchema(EmployeeBaseSchema):
    pass


class TransferSchema(ApiSchema):
    nullable_fields = {"decision_number", "decision_date", "note"}

    to_unit_id = fields.Integer(required=True, strict=True, error_messages=required)
    to_position_id = fields.Integer(required=True, strict=True, error_messages=required)
    effective_date = fields.Date(required=True, error_messages=required)
    assignment_type = fields.String(validate=validate.OneOf(sorted(ASSIGNMENT_TYPES)))
    decision_number = fields.String(allow_none=True)
    decision_date = fields.Date(allow_none=True)
    note = fields.String(allow_none=True)
    replace_existing = fields.Boolean(load_default=False)


class UnitBaseSchema(ApiSchema):
    nullable_fields = {"parent_id", "address", "phone", "email"}

    code = fields.String()
    name = fields.String()
    unit_type = fields.String(validate=validate.OneOf(sorted(UNIT_TYPES)))
    parent_id = fields.Integer(allow_none=True, strict=True)
    address = fields.String(allow_none=True)
    phone = fields.String(allow_none=True)
    email = fields.Email(allow_none=True)
    is_active = fields.Boolean()


class UnitCreateSchema(UnitBaseSchema):
    code = fields.String(required=True, error_messages=required)
    name = fields.String(required=True, error_messages=required)
    unit_type = fields.String(
        required=True,
        validate=validate.OneOf(sorted(UNIT_TYPES)),
        error_messages=required,
    )


class UnitUpdateSchema(UnitBaseSchema):
    pass


class PositionBaseSchema(ApiSchema):
    nullable_fields = {"description"}

    code = fields.String()
    name = fields.String()
    level = fields.Integer(strict=True)
    description = fields.String(allow_none=True)
    is_managerial = fields.Boolean()
    is_active = fields.Boolean()


class PositionCreateSchema(PositionBaseSchema):
    code = fields.String(required=True, error_messages=required)
    name = fields.String(required=True, error_messages=required)


class PositionUpdateSchema(PositionBaseSchema):
    pass


class PositionLimitCreateSchema(ApiSchema):
    nullable_fields = {"max_holders"}
    position_id = fields.Integer(required=True, strict=True, error_messages=required)
    max_holders = fields.Integer(allow_none=True, strict=True, validate=validate.Range(min=1))


class PositionLimitUpdateSchema(ApiSchema):
    nullable_fields = {"max_holders"}
    max_holders = fields.Integer(required=True, allow_none=True, strict=True)


class UserCreateSchema(ApiSchema):
    nullable_fields = {"email", "employee_id"}
    username = fields.String(required=True, error_messages=required)
    password = fields.String(required=True, validate=validate.Length(min=8), error_messages=required)
    full_name = fields.String(required=True, error_messages=required)
    email = fields.Email(allow_none=True)
    employee_id = fields.Integer(allow_none=True, strict=True)
    is_active = fields.Boolean()
    role_ids = fields.List(fields.Integer(strict=True))


class UserUpdateSchema(ApiSchema):
    nullable_fields = {"email", "employee_id"}
    full_name = fields.String()
    email = fields.Email(allow_none=True)
    employee_id = fields.Integer(allow_none=True, strict=True)
    is_active = fields.Boolean()


class ResetPasswordSchema(ApiSchema):
    new_password = fields.String(validate=validate.Length(min=8))


class UserRolesSchema(ApiSchema):
    role_ids = fields.List(fields.Integer(strict=True), required=True, error_messages=required)


class UnitScopeItemSchema(ApiSchema):
    nullable_fields = {"unit_id"}
    scope_type = fields.String(
        required=True,
        validate=validate.OneOf(["GLOBAL", "UNIT", "SUBTREE"]),
        error_messages=required,
    )
    unit_id = fields.Integer(allow_none=True, strict=True)


class UserScopesSchema(ApiSchema):
    scopes = fields.List(fields.Nested(UnitScopeItemSchema), required=True, error_messages=required)


class RoleBaseSchema(ApiSchema):
    nullable_fields = {"description"}
    name = fields.String()
    description = fields.String(allow_none=True)
    permissions = fields.List(fields.String())


class RoleCreateSchema(RoleBaseSchema):
    code = fields.String(required=True, error_messages=required)
    name = fields.String(required=True, error_messages=required)


class RoleUpdateSchema(RoleBaseSchema):
    pass


login_schema = LoginSchema()
change_password_schema = ChangePasswordSchema()
employee_create_schema = EmployeeCreateSchema()
employee_update_schema = EmployeeUpdateSchema()
transfer_schema = TransferSchema()
unit_create_schema = UnitCreateSchema()
unit_update_schema = UnitUpdateSchema()
position_create_schema = PositionCreateSchema()
position_update_schema = PositionUpdateSchema()
position_limit_create_schema = PositionLimitCreateSchema()
position_limit_update_schema = PositionLimitUpdateSchema()
user_create_schema = UserCreateSchema()
user_update_schema = UserUpdateSchema()
reset_password_schema = ResetPasswordSchema()
user_roles_schema = UserRolesSchema()
user_scopes_schema = UserScopesSchema()
role_create_schema = RoleCreateSchema()
role_update_schema = RoleUpdateSchema()
