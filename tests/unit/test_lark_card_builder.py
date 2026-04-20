"""
PM Digital Employee - Lark Card Builder Tests
Tests for LarkCardBuilder fluent API and static card factory methods.
"""

import pytest

from app.integrations.lark.schemas import LarkCardBuilder, LarkCardColor


class TestLarkCardBuilder:
    """Tests for LarkCardBuilder fluent API."""

    def test_build_empty_card(self):
        """Should build a minimal card with config."""
        card = LarkCardBuilder().build()

        assert "config" in card
        assert card["config"]["wide_screen_mode"] is True
        assert "elements" in card
        assert card["elements"] == []

    def test_set_header(self):
        """Should set header with title and color."""
        card = LarkCardBuilder().set_header("Test Title", "blue").build()

        assert "header" in card
        assert card["header"]["title"]["content"] == "Test Title"
        assert card["header"]["title"]["tag"] == "plain_text"
        assert card["header"]["template"] == "blue"

    def test_set_header_default_color(self):
        """Should use blue as default color."""
        card = LarkCardBuilder().set_header("Title").build()

        assert card["header"]["template"] == "blue"

    def test_add_markdown(self):
        """Should add markdown element."""
        card = LarkCardBuilder().add_markdown("**bold** text").build()

        assert len(card["elements"]) == 1
        assert card["elements"][0]["tag"] == "markdown"
        assert card["elements"][0]["content"] == "**bold** text"

    def test_add_divider(self):
        """Should add divider element."""
        card = LarkCardBuilder().add_divider().build()

        assert len(card["elements"]) == 1
        assert card["elements"][0]["tag"] == "hr"

    def test_add_field(self):
        """Should add field element."""
        card = LarkCardBuilder().add_field([
            {"content": "Field 1"},
            {"content": "Field 2"},
        ]).build()

        assert len(card["elements"]) == 1
        assert card["elements"][0]["tag"] == "field"
        assert len(card["elements"][0]["fields"]) == 2
        assert card["elements"][0]["fields"][0]["text"]["content"] == "Field 1"

    def test_add_action(self):
        """Should add action container."""
        actions = [
            {"tag": "button", "text": {"tag": "plain_text", "content": "OK"}, "type": "primary"},
        ]
        card = LarkCardBuilder().add_action(actions).build()

        assert len(card["elements"]) == 1
        assert card["elements"][0]["tag"] == "action"
        assert len(card["elements"][0]["actions"]) == 1

    def test_full_card(self):
        """Should build complete card with all elements."""
        card = (
            LarkCardBuilder()
            .set_header("Project Status", "green")
            .add_markdown("**Project Alpha** is on track.")
            .add_divider()
            .add_field([
                {"content": "Progress: 75%"},
                {"content": "Status: On Track"},
            ])
            .add_action([
                {"tag": "button", "text": {"tag": "plain_text", "content": "Details"}},
            ])
            .build()
        )

        assert card["header"]["title"]["content"] == "Project Status"
        assert card["header"]["template"] == "green"
        assert len(card["elements"]) == 4
        assert card["elements"][0]["tag"] == "markdown"
        assert card["elements"][1]["tag"] == "hr"
        assert card["elements"][2]["tag"] == "field"
        assert card["elements"][3]["tag"] == "action"

    def test_fluent_chaining(self):
        """Should support fluent method chaining."""
        builder = LarkCardBuilder()
        result = (
            builder
            .set_header("Title")
            .add_markdown("Content")
            .add_divider()
        )

        assert result is builder  # Returns self


class TestLarkCardBuilderCreateButton:
    """Tests for LarkCardBuilder.create_button static method."""

    def test_create_button_primary(self):
        """Should create primary button."""
        btn = LarkCardBuilder.create_button(
            text="Confirm",
            value={"action": "confirm"},
            style="primary",
        )

        assert btn["tag"] == "button"
        assert btn["text"]["content"] == "Confirm"
        assert btn["type"] == "primary"
        assert btn["value"] == {"action": "confirm"}

    def test_create_button_danger(self):
        """Should create danger button."""
        btn = LarkCardBuilder.create_button(
            text="Delete",
            value={"action": "delete"},
            style="danger",
        )

        assert btn["type"] == "danger"

    def test_create_button_default(self):
        """Should create default button."""
        btn = LarkCardBuilder.create_button(
            text="Cancel",
            value={"action": "cancel"},
            style="default",
        )

        assert btn["type"] == "default"

    def test_create_button_style_mapping(self):
        """Should map color names to proper styles."""
        btn_green = LarkCardBuilder.create_button("Go", {"action": "go"}, style="green")
        btn_red = LarkCardBuilder.create_button("Stop", {"action": "stop"}, style="red")
        btn_blue = LarkCardBuilder.create_button("Info", {"action": "info"}, style="blue")

        assert btn_green["type"] == "primary"
        assert btn_red["type"] == "danger"
        assert btn_blue["type"] == "primary"


class TestLarkCardBuilderCreateTextNotice:
    """Tests for LarkCardBuilder.create_text_notice static method."""

    def test_text_notice_basic(self):
        """Should create text notice with title and description."""
        card = LarkCardBuilder.create_text_notice(
            title="Notice",
            desc="This is a test notice.",
        )

        assert card["header"]["title"]["content"] == "Notice"
        assert len(card["elements"]) >= 1

    def test_text_notice_with_source(self):
        """Should include source description when provided."""
        card = LarkCardBuilder.create_text_notice(
            title="Notice",
            desc="Content here.",
            source_desc="PM Digital Employee",
        )

        # Should have divider + source markdown
        assert any(el.get("tag") == "hr" for el in card["elements"])


class TestLarkCardBuilderCreateButtonInteraction:
    """Tests for LarkCardBuilder.create_button_interaction static method."""

    def test_button_interaction(self):
        """Should create card with buttons."""
        card = LarkCardBuilder.create_button_interaction(
            title="Confirm Action",
            desc="Do you want to proceed?",
            buttons=[
                {"text": "Yes", "key": "confirm:action"},
                {"text": "No", "key": "cancel"},
            ],
        )

        assert card["header"]["title"]["content"] == "Confirm Action"
        # Find action element
        action_el = next(
            (el for el in card["elements"] if el.get("tag") == "action"),
            None,
        )
        assert action_el is not None
        assert len(action_el["actions"]) == 2

    def test_button_interaction_confirm_style(self):
        """Confirm buttons should be primary style."""
        card = LarkCardBuilder.create_button_interaction(
            title="Test",
            desc="Test",
            buttons=[
                {"text": "Confirm", "key": "confirm:skill"},
            ],
        )

        action_el = next(
            (el for el in card["elements"] if el.get("tag") == "action"),
            None,
        )
        assert action_el["actions"][0]["type"] == "primary"


class TestLarkCardColor:
    """Tests for LarkCardColor enum."""

    def test_all_colors(self):
        """All expected colors should be available."""
        colors = [c.value for c in LarkCardColor]
        assert "blue" in colors
        assert "green" in colors
        assert "red" in colors
        assert "orange" in colors
        assert "purple" in colors
        assert "indigo" in colors
        assert "grey" in colors
        assert "turquoise" in colors
        assert "yellow" in colors
        assert "primary" in colors
        assert "danger" in colors
        assert "warning" in colors
        assert "success" in colors
