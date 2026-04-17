
CREATE TABLE audit_logs (
	id UUID NOT NULL, 
	trace_id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64), 
	user_name VARCHAR(128), 
	project_id UUID, 
	action VARCHAR(64) NOT NULL, 
	resource_type VARCHAR(64), 
	resource_id VARCHAR(128), 
	result VARCHAR(32) NOT NULL, 
	error_message TEXT, 
	details TEXT, 
	request_params TEXT, 
	response_summary TEXT, 
	ip_address VARCHAR(64), 
	user_agent VARCHAR(512), 
	duration_ms INTEGER, 
	skill_name VARCHAR(64), 
	llm_model VARCHAR(64), 
	llm_tokens_input INTEGER, 
	llm_tokens_output INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	created_by VARCHAR(50), 
	updated_by VARCHAR(50), 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX ix_audit_logs_action ON audit_logs (action);
CREATE INDEX ix_audit_logs_project_id ON audit_logs (project_id);
CREATE INDEX ix_audit_logs_project_created ON audit_logs (project_id, created_at);
CREATE INDEX ix_audit_logs_trace_id ON audit_logs (trace_id);
CREATE INDEX ix_audit_logs_action ON audit_logs (action);
CREATE INDEX ix_audit_logs_trace_id ON audit_logs (trace_id);
CREATE INDEX ix_audit_logs_project_id ON audit_logs (project_id);

CREATE TABLE event_records (
	id UUID NOT NULL, 
	event_id VARCHAR(128) NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	project_id UUID, 
	source VARCHAR(64), 
	source_event_id VARCHAR(128), 
	data TEXT, 
	metadata_json TEXT, 
	user_id VARCHAR(64), 
	status VARCHAR(32) NOT NULL, 
	retry_count INTEGER NOT NULL, 
	max_retries INTEGER NOT NULL, 
	processed_at DATETIME, 
	result TEXT, 
	error_message TEXT, 
	scheduled_at DATETIME, 
	trace_id VARCHAR(64), 
	created_at DATETIME, 
	updated_at DATETIME, 
	created_by VARCHAR(50), 
	updated_by VARCHAR(50), 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_event_records_project_id ON event_records (project_id);
CREATE UNIQUE INDEX ix_event_records_event_id ON event_records (event_id);
CREATE INDEX ix_event_records_event_type ON event_records (event_type);
CREATE UNIQUE INDEX ix_event_records_event_id ON event_records (event_id);
CREATE INDEX ix_event_records_project_id ON event_records (project_id);
CREATE INDEX ix_event_records_event_type ON event_records (event_type);
CREATE INDEX ix_event_records_status ON event_records (status);
CREATE INDEX ix_event_records_created_at ON event_records (created_at);

CREATE TABLE knowledge_documents (
	id UUID NOT NULL, 
	title VARCHAR(512) NOT NULL, 
	content TEXT NOT NULL, 
	content_type VARCHAR(64), 
	scope_type VARCHAR(32) NOT NULL, 
	department_id VARCHAR(64), 
	project_id UUID, 
	embedding TEXT, 
	source_url VARCHAR(1024), 
	source_file VARCHAR(512), 
	doc_type VARCHAR(64), 
	metadata_json TEXT, 
	section_path VARCHAR(512), 
	chunk_index INTEGER, 
	parent_doc_id UUID, 
	is_active BOOLEAN NOT NULL, 
	version INTEGER NOT NULL, 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_knowledge_documents_department_id ON knowledge_documents (department_id);
CREATE INDEX ix_knowledge_documents_project_id ON knowledge_documents (project_id);
CREATE INDEX ix_knowledge_documents_is_active ON knowledge_documents (is_active);
CREATE INDEX ix_knowledge_documents_scope_type ON knowledge_documents (scope_type);
CREATE INDEX ix_knowledge_documents_project_id ON knowledge_documents (project_id);
CREATE INDEX ix_knowledge_documents_department_id ON knowledge_documents (department_id);
CREATE INDEX ix_knowledge_documents_doc_type ON knowledge_documents (doc_type);
CREATE INDEX ix_knowledge_documents_scope_type ON knowledge_documents (scope_type);
CREATE INDEX ix_knowledge_documents_doc_type ON knowledge_documents (doc_type);

CREATE TABLE llm_usage_logs (
	id UUID NOT NULL, 
	trace_id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64), 
	model VARCHAR(64) NOT NULL, 
	provider VARCHAR(32), 
	prompt_tokens INTEGER NOT NULL, 
	completion_tokens INTEGER NOT NULL, 
	total_tokens INTEGER NOT NULL, 
	latency_ms INTEGER NOT NULL, 
	skill_name VARCHAR(64), 
	success BOOLEAN NOT NULL, 
	error_message VARCHAR(1024), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_llm_usage_model ON llm_usage_logs (model);
CREATE INDEX ix_llm_usage_created_at ON llm_usage_logs (created_at);
CREATE INDEX ix_llm_usage_logs_model ON llm_usage_logs (model);
CREATE INDEX ix_llm_usage_user_date ON llm_usage_logs (user_id, created_at);
CREATE INDEX ix_llm_usage_logs_provider ON llm_usage_logs (provider);
CREATE INDEX ix_llm_usage_trace_id ON llm_usage_logs (trace_id);
CREATE INDEX ix_llm_usage_logs_user_id ON llm_usage_logs (user_id);
CREATE INDEX ix_llm_usage_logs_trace_id ON llm_usage_logs (trace_id);
CREATE INDEX ix_llm_usage_provider ON llm_usage_logs (provider);

CREATE TABLE project_skill_switches (
	id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	skill_id UUID NOT NULL, 
	is_enabled BOOLEAN NOT NULL, 
	enabled_by VARCHAR(64), 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_project_skill_switches_project_id ON project_skill_switches (project_id);
CREATE INDEX ix_project_skill_switches_skill_id ON project_skill_switches (skill_id);
CREATE INDEX ix_project_skill_switches_skill_id ON project_skill_switches (skill_id);
CREATE UNIQUE INDEX uq_project_skill ON project_skill_switches (project_id, skill_id);
CREATE INDEX ix_project_skill_switches_project_id ON project_skill_switches (project_id);

CREATE TABLE projects (
	id UUID NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	code VARCHAR(64) NOT NULL, 
	description TEXT, 
	status VARCHAR(32) NOT NULL, 
	project_type VARCHAR(64), 
	priority INTEGER, 
	start_date DATE, 
	end_date DATE, 
	actual_start_date DATE, 
	actual_end_date DATE, 
	total_budget NUMERIC(18, 2), 
	pm_id UUID, 
	pm_name VARCHAR(128), 
	department_id UUID, 
	department_name VARCHAR(256), 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	created_by VARCHAR(50), 
	updated_by VARCHAR(50), 
	PRIMARY KEY (id), 
	UNIQUE (code)
)

;
CREATE UNIQUE INDEX ix_projects_code ON projects (code);
CREATE INDEX ix_projects_pm_id ON projects (pm_id);
CREATE INDEX ix_projects_pm_id ON projects (pm_id);
CREATE INDEX ix_projects_department_id ON projects (department_id);
CREATE INDEX ix_projects_start_date ON projects (start_date);
CREATE INDEX ix_projects_status ON projects (status);
CREATE INDEX ix_projects_department_id ON projects (department_id);

CREATE TABLE retrieval_traces (
	id UUID NOT NULL, 
	trace_id VARCHAR(64) NOT NULL, 
	query TEXT NOT NULL, 
	query_embedding_preview VARCHAR(128), 
	user_id VARCHAR(64), 
	project_id UUID, 
	top_k INTEGER NOT NULL, 
	similarity_threshold FLOAT, 
	hits TEXT, 
	hit_count INTEGER NOT NULL, 
	latency_ms FLOAT, 
	embedding_latency_ms FLOAT, 
	rerank_latency_ms FLOAT, 
	permission_filtered_count INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	created_by VARCHAR(50), 
	updated_by VARCHAR(50), 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_retrieval_traces_user_id ON retrieval_traces (user_id);
CREATE INDEX ix_retrieval_traces_created_at ON retrieval_traces (created_at);
CREATE INDEX ix_retrieval_traces_project_id ON retrieval_traces (project_id);
CREATE INDEX ix_retrieval_traces_user_id ON retrieval_traces (user_id);
CREATE INDEX ix_retrieval_traces_project_id ON retrieval_traces (project_id);
CREATE INDEX ix_retrieval_traces_trace_id ON retrieval_traces (trace_id);
CREATE INDEX ix_retrieval_traces_trace_id ON retrieval_traces (trace_id);

CREATE TABLE skill_definitions (
	id UUID NOT NULL, 
	skill_name VARCHAR(64) NOT NULL, 
	display_name VARCHAR(128) NOT NULL, 
	description TEXT NOT NULL, 
	manifest TEXT NOT NULL, 
	version VARCHAR(32) NOT NULL, 
	domain VARCHAR(64) NOT NULL, 
	is_enabled BOOLEAN NOT NULL, 
	enabled_by_default BOOLEAN NOT NULL, 
	input_schema TEXT, 
	output_schema TEXT, 
	allowed_roles TEXT, 
	required_permissions TEXT, 
	supports_async BOOLEAN NOT NULL, 
	supports_confirmation BOOLEAN NOT NULL, 
	timeout_seconds INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (skill_name)
)

;
CREATE UNIQUE INDEX ix_skill_definitions_skill_name ON skill_definitions (skill_name);
CREATE INDEX ix_skill_definitions_is_enabled ON skill_definitions (is_enabled);
CREATE INDEX ix_skill_definitions_domain ON skill_definitions (domain);

CREATE TABLE users (
	id UUID NOT NULL, 
	lark_user_id VARCHAR(64) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	email VARCHAR(256), 
	phone VARCHAR(32), 
	avatar_url VARCHAR(512), 
	department_id VARCHAR(64), 
	department_name VARCHAR(256), 
	position VARCHAR(128), 
	is_active BOOLEAN NOT NULL, 
	is_admin BOOLEAN NOT NULL, 
	last_login_at DATETIME, 
	created_at DATETIME, 
	updated_at DATETIME, 
	created_by VARCHAR(50), 
	updated_by VARCHAR(50), 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_users_department_id ON users (department_id);
CREATE UNIQUE INDEX ix_users_lark_user_id ON users (lark_user_id);
CREATE UNIQUE INDEX ix_users_lark_user_id ON users (lark_user_id);
CREATE INDEX ix_users_department_id ON users (department_id);
CREATE INDEX ix_users_is_active ON users (is_active);

CREATE TABLE approval_workflows (
	id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	type VARCHAR(32) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	title VARCHAR(512) NOT NULL, 
	content TEXT, 
	applicant_id VARCHAR(64) NOT NULL, 
	applicant_name VARCHAR(128), 
	current_approver_id VARCHAR(64), 
	current_approver_name VARCHAR(128), 
	result VARCHAR(32), 
	comment TEXT, 
	document_id UUID, 
	submitted_at DATETIME NOT NULL, 
	completed_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;
CREATE INDEX ix_approval_workflows_project_id ON approval_workflows (project_id);
CREATE INDEX ix_approval_workflows_applicant_id ON approval_workflows (applicant_id);
CREATE INDEX ix_approval_workflows_type ON approval_workflows (type);
CREATE INDEX ix_approval_workflows_project_id ON approval_workflows (project_id);
CREATE INDEX ix_approval_workflows_status ON approval_workflows (status);
CREATE INDEX ix_approval_workflows_applicant_id ON approval_workflows (applicant_id);
CREATE INDEX ix_approval_workflows_current_approver_id ON approval_workflows (current_approver_id);
CREATE INDEX ix_approval_workflows_current_approver_id ON approval_workflows (current_approver_id);

CREATE TABLE conversation_sessions (
	id UUID NOT NULL, 
	project_id UUID, 
	user_id VARCHAR(64) NOT NULL, 
	user_name VARCHAR(128), 
	chat_id VARCHAR(64) NOT NULL, 
	chat_type VARCHAR(32), 
	state VARCHAR(32) NOT NULL, 
	matched_skill VARCHAR(64), 
	collected_params TEXT, 
	missing_params TEXT, 
	context TEXT, 
	round_count INTEGER NOT NULL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	created_by VARCHAR(50), 
	updated_by VARCHAR(50), 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE SET NULL
)

;
CREATE INDEX ix_conversation_sessions_state ON conversation_sessions (state);
CREATE INDEX ix_conversation_sessions_user_id ON conversation_sessions (user_id);
CREATE INDEX ix_conversation_sessions_user_id ON conversation_sessions (user_id);
CREATE INDEX ix_conversation_sessions_project_id ON conversation_sessions (project_id);
CREATE INDEX ix_conversation_sessions_chat_id ON conversation_sessions (chat_id);
CREATE INDEX ix_conversation_sessions_chat_id ON conversation_sessions (chat_id);
CREATE INDEX ix_conversation_sessions_project_id ON conversation_sessions (project_id);

CREATE TABLE group_project_bindings (
	id UUID NOT NULL, 
	chat_id VARCHAR(64) NOT NULL, 
	chat_name VARCHAR(256), 
	project_id UUID NOT NULL, 
	bound_at DATETIME NOT NULL, 
	bound_by VARCHAR(64), 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_group_chat_id UNIQUE (chat_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;
CREATE UNIQUE INDEX ix_group_project_bindings_chat_id ON group_project_bindings (chat_id);
CREATE INDEX ix_group_project_bindings_chat_id ON group_project_bindings (chat_id);
CREATE INDEX ix_group_project_bindings_project_id ON group_project_bindings (project_id);
CREATE INDEX ix_group_project_bindings_project_id ON group_project_bindings (project_id);
CREATE INDEX ix_group_project_bindings_is_active ON group_project_bindings (is_active);

CREATE TABLE milestones (
	id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	description TEXT, 
	status VARCHAR(32) NOT NULL, 
	due_date DATE NOT NULL, 
	achieved_date DATE, 
	is_key_milestone BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;
CREATE INDEX ix_milestones_project_id ON milestones (project_id);
CREATE INDEX ix_milestones_due_date ON milestones (due_date);
CREATE INDEX ix_milestones_project_status ON milestones (project_id, status);
CREATE INDEX ix_milestones_project_id ON milestones (project_id);
CREATE INDEX ix_milestones_status ON milestones (status);

CREATE TABLE project_cost_actuals (
	id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	category VARCHAR(32) NOT NULL, 
	amount NUMERIC(18, 2) NOT NULL, 
	expense_date DATE NOT NULL, 
	description TEXT, 
	invoice_number VARCHAR(128), 
	approval_status VARCHAR(32), 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;
CREATE INDEX ix_project_cost_actuals_project_id ON project_cost_actuals (project_id);
CREATE INDEX ix_project_cost_actuals_expense_date ON project_cost_actuals (expense_date);
CREATE INDEX ix_project_cost_actuals_project_id ON project_cost_actuals (project_id);
CREATE INDEX ix_project_cost_actuals_category ON project_cost_actuals (category);

CREATE TABLE project_cost_budgets (
	id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	category VARCHAR(32) NOT NULL, 
	amount NUMERIC(18, 2) NOT NULL, 
	description TEXT, 
	fiscal_year INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;
CREATE INDEX ix_project_cost_budgets_fiscal_year ON project_cost_budgets (fiscal_year);
CREATE INDEX ix_project_cost_budgets_project_id ON project_cost_budgets (project_id);
CREATE INDEX ix_project_cost_budgets_category ON project_cost_budgets (category);
CREATE INDEX ix_project_cost_budgets_project_id ON project_cost_budgets (project_id);

CREATE TABLE project_documents (
	id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	name VARCHAR(512) NOT NULL, 
	type VARCHAR(32) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	file_path VARCHAR(1024), 
	file_url VARCHAR(1024), 
	file_size INTEGER, 
	file_type VARCHAR(64), 
	version INTEGER NOT NULL, 
	content TEXT, 
	summary TEXT, 
	author_id VARCHAR(64), 
	author_name VARCHAR(128), 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;
CREATE INDEX ix_project_documents_project_id ON project_documents (project_id);
CREATE INDEX ix_project_documents_type ON project_documents (type);
CREATE INDEX ix_project_documents_status ON project_documents (status);
CREATE INDEX ix_project_documents_project_type ON project_documents (project_id, type);
CREATE INDEX ix_project_documents_project_id ON project_documents (project_id);

CREATE TABLE project_risks (
	id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	code VARCHAR(32), 
	title VARCHAR(512) NOT NULL, 
	description TEXT, 
	category VARCHAR(32) NOT NULL, 
	level VARCHAR(32) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	probability INTEGER NOT NULL, 
	impact INTEGER NOT NULL, 
	identified_date DATE NOT NULL, 
	due_date DATE, 
	resolved_date DATE, 
	mitigation_plan TEXT, 
	mitigation_status VARCHAR(32), 
	owner_id VARCHAR(64), 
	owner_name VARCHAR(128), 
	root_cause TEXT, 
	ai_suggestion TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;
CREATE INDEX ix_project_risks_project_level ON project_risks (project_id, level);
CREATE INDEX ix_project_risks_level ON project_risks (level);
CREATE INDEX ix_project_risks_project_id ON project_risks (project_id);
CREATE INDEX ix_project_risks_status ON project_risks (status);
CREATE INDEX ix_project_risks_category ON project_risks (category);
CREATE INDEX ix_project_risks_project_id ON project_risks (project_id);

CREATE TABLE tasks (
	id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	code VARCHAR(64), 
	name VARCHAR(512) NOT NULL, 
	description TEXT, 
	status VARCHAR(32) NOT NULL, 
	priority VARCHAR(32) NOT NULL, 
	progress INTEGER NOT NULL, 
	start_date DATE, 
	end_date DATE, 
	actual_start_date DATE, 
	actual_end_date DATE, 
	estimated_hours NUMERIC(10, 2), 
	actual_hours NUMERIC(10, 2), 
	assignee_id VARCHAR(64), 
	assignee_name VARCHAR(128), 
	parent_task_id UUID, 
	deliverable VARCHAR(512), 
	wbs_code VARCHAR(64), 
	level INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE, 
	FOREIGN KEY(parent_task_id) REFERENCES tasks (id) ON DELETE SET NULL
)

;
CREATE INDEX ix_tasks_parent_task_id ON tasks (parent_task_id);
CREATE INDEX ix_tasks_status ON tasks (status);
CREATE INDEX ix_tasks_assignee_id ON tasks (assignee_id);
CREATE INDEX ix_tasks_end_date ON tasks (end_date);
CREATE INDEX ix_tasks_parent_task_id ON tasks (parent_task_id);
CREATE INDEX ix_tasks_project_id ON tasks (project_id);
CREATE INDEX ix_tasks_project_status ON tasks (project_id, status);
CREATE INDEX ix_tasks_assignee_id ON tasks (assignee_id);
CREATE INDEX ix_tasks_project_id ON tasks (project_id);

CREATE TABLE user_project_roles (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	joined_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_project UNIQUE (user_id, project_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;
CREATE INDEX ix_user_project_roles_project_id ON user_project_roles (project_id);
CREATE INDEX ix_user_project_roles_user_id ON user_project_roles (user_id);
CREATE INDEX ix_user_project_roles_user_id ON user_project_roles (user_id);
CREATE INDEX ix_user_project_roles_project_id ON user_project_roles (project_id);
CREATE INDEX ix_user_project_roles_role ON user_project_roles (role);

CREATE TABLE conversation_messages (
	id UUID NOT NULL, 
	session_id UUID NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	content TEXT NOT NULL, 
	skill_name VARCHAR(64), 
	execution_id UUID, 
	metadata_json TEXT, 
	created_at DATETIME, 
	updated_at DATETIME, 
	created_by VARCHAR(50), 
	updated_by VARCHAR(50), 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES conversation_sessions (id) ON DELETE CASCADE
)

;
CREATE INDEX ix_conversation_messages_session_id ON conversation_messages (session_id);
CREATE INDEX ix_conversation_messages_created_at ON conversation_messages (created_at);
CREATE INDEX ix_conversation_messages_session_id ON conversation_messages (session_id);
