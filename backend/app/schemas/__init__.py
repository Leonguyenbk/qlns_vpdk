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
from ..models.survey import QUESTION_TYPES


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
        # hồ sơ mở rộng
        "place_of_origin", "identity_issued_date", "identity_issued_place",
        "job_grade_code", "job_grade_name", "job_duties", "tenure_date", "contract_type",
        "education_level", "education_major", "education_mode",
        "foreign_language_cert", "it_cert",
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

    # --- Hồ sơ mở rộng (nguồn: biểu "Phụ lục 4") ---
    place_of_origin = fields.String(allow_none=True)
    identity_issued_date = fields.Date(allow_none=True)
    identity_issued_place = fields.String(allow_none=True)
    job_grade_code = fields.String(allow_none=True)
    job_grade_name = fields.String(allow_none=True)
    job_duties = fields.String(allow_none=True)
    tenure_date = fields.Date(allow_none=True)
    contract_type = fields.String(allow_none=True)
    education_level = fields.String(allow_none=True)
    education_major = fields.String(allow_none=True)
    education_mode = fields.String(allow_none=True)
    foreign_language_cert = fields.String(allow_none=True)
    it_cert = fields.String(allow_none=True)


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
    # Cho phép sửa cả đơn vị / chức vụ của phân công chính (cập nhật tại chỗ).
    unit_id = fields.Integer(allow_none=True, strict=False)
    position_id = fields.Integer(allow_none=True, strict=False)

    nullable_fields = EmployeeBaseSchema.nullable_fields | {"unit_id", "position_id"}


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


class AnnouncementCreateSchema(ApiSchema):
    nullable_fields = {"expires_at"}
    title = fields.String(required=True, validate=validate.Length(min=1, max=255), error_messages=required)
    content = fields.String(required=True, validate=validate.Length(min=1), error_messages=required)
    category = fields.String(load_default="Thông báo", validate=validate.Length(max=50))
    audience_type = fields.String(load_default="ALL", validate=validate.OneOf(["ALL", "UNIT", "ROLE", "USER"]))
    audience_ids = fields.List(fields.Integer(strict=True), load_default=list)
    is_pinned = fields.Boolean(load_default=False)
    expires_at = fields.DateTime(allow_none=True)


class AnnouncementUpdateSchema(ApiSchema):
    nullable_fields = {"expires_at"}
    title = fields.String(validate=validate.Length(min=1, max=255))
    content = fields.String(validate=validate.Length(min=1))
    category = fields.String(validate=validate.Length(max=50))
    audience_type = fields.String(validate=validate.OneOf(["ALL", "UNIT", "ROLE", "USER"]))
    audience_ids = fields.List(fields.Integer(strict=True))
    is_pinned = fields.Boolean()
    expires_at = fields.DateTime(allow_none=True)


class AnnouncementStatusSchema(ApiSchema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(["published", "archived"]),
        error_messages=required,
    )


class SurveyCreateSchema(ApiSchema):
    nullable_fields = {"description", "welcome_message", "start_at", "end_at"}
    title = fields.String(required=True, error_messages=required)
    description = fields.String(allow_none=True)
    welcome_message = fields.String(allow_none=True)
    is_anonymous = fields.Boolean(load_default=True)
    start_at = fields.DateTime(allow_none=True)
    end_at = fields.DateTime(allow_none=True)


class SurveyUpdateSchema(ApiSchema):
    nullable_fields = {"description", "welcome_message", "start_at", "end_at"}
    title = fields.String()
    description = fields.String(allow_none=True)
    welcome_message = fields.String(allow_none=True)
    is_anonymous = fields.Boolean()
    start_at = fields.DateTime(allow_none=True)
    end_at = fields.DateTime(allow_none=True)


class SurveyBranchLimitItemSchema(ApiSchema):
    nullable_fields = {"max_responses"}
    branch_id = fields.Integer(required=True, strict=True, error_messages=required)
    max_responses = fields.Integer(allow_none=True, strict=True)


class SurveyBranchLimitsSchema(ApiSchema):
    items = fields.List(fields.Nested(SurveyBranchLimitItemSchema), required=True, error_messages=required)


class SurveyStatusSchema(ApiSchema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(["draft", "active", "paused", "closed", "archived"]),
        error_messages=required,
    )


class SurveyOptionInputSchema(ApiSchema):
    nullable_fields = {"option_value", "score"}
    option_text = fields.String(required=True, error_messages=required)
    option_value = fields.String(allow_none=True)
    score = fields.Float(allow_none=True)


class SurveySectionCreateSchema(ApiSchema):
    title = fields.String(required=True, error_messages=required)


class SurveySectionUpdateSchema(ApiSchema):
    title = fields.String()


class SurveyQuestionCreateSchema(ApiSchema):
    nullable_fields = {"section", "section_id", "yes_score", "no_score"}
    question_text = fields.String(required=True, error_messages=required)
    question_type = fields.String(
        required=True, validate=validate.OneOf(sorted(QUESTION_TYPES)), error_messages=required
    )
    is_required = fields.Boolean(load_default=False)
    is_active = fields.Boolean(load_default=True)
    section = fields.String(allow_none=True)
    section_id = fields.Integer(allow_none=True, strict=True)
    yes_score = fields.Float(allow_none=True)
    no_score = fields.Float(allow_none=True)
    options = fields.List(fields.Nested(SurveyOptionInputSchema), load_default=list)


class SurveyQuestionUpdateSchema(ApiSchema):
    nullable_fields = {"section", "section_id", "yes_score", "no_score"}
    question_text = fields.String()
    question_type = fields.String(validate=validate.OneOf(sorted(QUESTION_TYPES)))
    is_required = fields.Boolean()
    is_active = fields.Boolean()
    section = fields.String(allow_none=True)
    section_id = fields.Integer(allow_none=True, strict=True)
    yes_score = fields.Float(allow_none=True)
    no_score = fields.Float(allow_none=True)
    options = fields.List(fields.Nested(SurveyOptionInputSchema))


class SurveyOptionCreateSchema(ApiSchema):
    nullable_fields = {"option_value", "score"}
    option_text = fields.String(required=True, error_messages=required)
    option_value = fields.String(allow_none=True)
    score = fields.Float(allow_none=True)


class SurveyOptionUpdateSchema(ApiSchema):
    nullable_fields = {"option_value", "score"}
    option_text = fields.String()
    option_value = fields.String(allow_none=True)
    score = fields.Float(allow_none=True)


class ReorderItemSchema(ApiSchema):
    id = fields.Integer(required=True, strict=True, error_messages=required)
    sort_order = fields.Integer(required=True, strict=True, error_messages=required)


class ReorderSchema(ApiSchema):
    items = fields.List(fields.Nested(ReorderItemSchema), required=True, error_messages=required)


class SurveyAnswerItemSchema(ApiSchema):
    nullable_fields = {"option_id", "answer_text", "answer_number"}
    question_id = fields.Integer(required=True, strict=True, error_messages=required)
    option_id = fields.Integer(allow_none=True, strict=True)
    option_ids = fields.List(fields.Integer(strict=True))
    answer_text = fields.String(allow_none=True)
    answer_number = fields.Float(allow_none=True)


class SurveySubmitSchema(ApiSchema):
    nullable_fields = {
        "respondent_name", "respondent_phone", "respondent_email", "respondent_address",
        "branch_id", "service_id", "counter_id", "employee_id", "client_token",
    }
    respondent_name = fields.String(allow_none=True)
    respondent_phone = fields.String(allow_none=True)
    respondent_email = fields.String(allow_none=True)
    respondent_address = fields.String(allow_none=True)
    branch_id = fields.Integer(allow_none=True, strict=True)
    service_id = fields.Integer(allow_none=True, strict=True)
    counter_id = fields.Integer(allow_none=True, strict=True)
    employee_id = fields.Integer(allow_none=True, strict=True)
    client_token = fields.String(allow_none=True)
    answers = fields.List(fields.Nested(SurveyAnswerItemSchema), required=True, error_messages=required)


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
announcement_create_schema = AnnouncementCreateSchema()
announcement_update_schema = AnnouncementUpdateSchema()
announcement_status_schema = AnnouncementStatusSchema()

survey_create_schema = SurveyCreateSchema()
survey_update_schema = SurveyUpdateSchema()
survey_status_schema = SurveyStatusSchema()
survey_branch_limits_schema = SurveyBranchLimitsSchema()
survey_section_create_schema = SurveySectionCreateSchema()
survey_section_update_schema = SurveySectionUpdateSchema()
survey_question_create_schema = SurveyQuestionCreateSchema()
survey_question_update_schema = SurveyQuestionUpdateSchema()
survey_option_create_schema = SurveyOptionCreateSchema()
survey_option_update_schema = SurveyOptionUpdateSchema()
reorder_schema = ReorderSchema()
survey_submit_schema = SurveySubmitSchema()
