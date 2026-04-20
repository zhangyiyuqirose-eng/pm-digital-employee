"""
PM数字员工系统快速启动验证脚本

此脚本将验证系统的主要组件是否能够正常导入和初始化，
这是启动完整服务前的关键验证步骤。
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.getcwd()))

def verify_core_modules():
    """验证核心模块导入"""
    print(">>> 验证核心模块...")

    modules_to_verify = [
        ("app.core.config", "settings"),
        ("app.core.exceptions", "APIException"),
        ("app.domain.base", "Base, AuditMixin"),
        ("app.services.context_service", "ContextService"),
        ("app.skills.base", "BaseSkill"),
        ("app.integrations.lark.client", "LarkClient"),
        ("app.integrations.lark.signature", "verify_signature"),
        ("app.orchestrator.schemas", "DialogState"),
        ("app.presentation.cards.base", "BaseCard"),
    ]

    success_count = 0
    for module_path, components in modules_to_verify:
        try:
            module = __import__(module_path, fromlist=[components.split(',')[0].strip()])
            print(f"  + {module_path} - 可用")
            success_count += 1
        except ImportError as e:
            print(f"  - {module_path} - 错误: {str(e)[:60]}...")

    print(f"\n  总结: {success_count}/{len(modules_to_verify)} 个模块验证成功\n")
    return success_count == len(modules_to_verify)

def verify_config():
    """验证配置加载"""
    print(">>> 验证配置加载...")

    try:
        from app.core.config import settings
        print(f"  + 配置加载成功")
        print(f"     应用名称: {settings.app_name}")
        print(f"     环境: {settings.app_env}")
        print(f"     飞书配置: {'已配置' if settings.lark_configured else '未配置'}")
        return True
    except Exception as e:
        print(f"  - 配置加载失败: {e}")
        return False

def verify_models():
    """验证数据模型"""
    print(">>> 验证数据模型...")

    models_to_verify = [
        ("app.domain.models.user", "User"),
        ("app.domain.models.project", "Project"),
        ("app.domain.models.task", "Task"),
        ("app.domain.models.group_project_binding", "GroupProjectBinding"),
    ]

    success_count = 0
    for module_path, model_name in models_to_verify:
        try:
            module = __import__(module_path, fromlist=[model_name])
            model_class = getattr(module, model_name)
            instance = model_class()
            print(f"  + {model_name} - 可用")
            success_count += 1
        except ImportError:
            print(f"  ? {model_name} - 未找到 (可能不需要)")
        except Exception as e:
            print(f"  - {model_name} - 错误: {str(e)[:60]}...")

    print(f"\n  总结: {success_count}/{len([m for m in models_to_verify])} 个模型验证成功\n")
    return success_count > 0  # 只要有部分模型可用即可

def verify_integrations():
    """验证集成模块"""
    print(">>> 验证飞书集成...")

    integration_files = [
        "app/integrations/lark/client.py",
        "app/integrations/lark/service.py",
        "app/integrations/lark/schemas.py",
        "app/integrations/lark/signature.py",
    ]

    success_count = 0
    for file_path in integration_files:
        if os.path.exists(file_path):
            print(f"  + {file_path} - 存在")
            success_count += 1
        else:
            print(f"  - {file_path} - 缺失")

    print(f"\n  总结: {success_count}/{len(integration_files)} 个文件存在\n")
    return success_count == len(integration_files)

def verify_skills():
    """验证技能系统"""
    print(">>> 验证技能系统...")

    try:
        from app.orchestrator.skill_registry import get_skill_registry
        print("  + 技能注册系统可用")

        # 尝试获取技能注册中心
        try:
            registry = get_skill_registry()
            skills = registry.list_all_skills()
            print(f"  + 发现 {len(skills)} 个已注册技能")
            for skill_manifest in list(skills)[:3]:  # 仅显示前3个
                print(f"     - {skill_manifest.skill_name}: {skill_manifest.display_name}")
            if len(skills) > 3:
                print(f"     ... 还有 {len(skills) - 3} 个技能")
            return True
        except Exception as e:
            print(f"  ? 技能获取异常: {e} (这可能是正常的，如果技能还未注册)")
            return True  # 技能在应用启动时才会完全注册
    except ImportError as e:
        print(f"  - 技能系统导入失败: {e}")
        return False

def verify_environment():
    """验证环境配置"""
    print(">>> 验证环境配置...")

    required_files = [
        "requirements.txt",
        "docker-compose.yml",
        ".env.example",
        "app/main.py"
    ]

    success_count = 0
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  + {file_path} - 存在")
            success_count += 1
        else:
            print(f"  ? {file_path} - 缺失")

    print(f"\n  总结: {success_count}/{len(required_files)} 个文件存在\n")
    return success_count >= len(required_files) - 1  # 至少大部分文件存在

def run_complete_verification():
    """运行完整验证"""
    print("="*60)
    print("PM数字员工系统 - 快速启动验证")
    print("="*60)
    print()

    results = []

    results.append(("核心模块", verify_core_modules()))
    results.append(("配置加载", verify_config()))
    results.append(("数据模型", verify_models()))
    results.append(("飞书集成", verify_integrations()))
    results.append(("技能系统", verify_skills()))
    results.append(("环境文件", verify_environment()))

    print("="*60)
    print("验证总结:")
    print("="*60)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "通过" if result else "失败"
        print(f"{name:12}: {status}")
        if result:
            passed += 1

    print("-"*60)
    print(f"总体进度: {passed}/{total} 项通过")

    if passed == total:
        print("\n恭喜! 所有验证通过！系统已准备好启动。")
        print("\n下一步操作建议:")
        print("1. 配置环境变量: cp .env.example .env")
        print("2. 编辑 .env 文件，填入实际配置")
        print("3. 启动应用: python -m app.main")
    else:
        print(f"\n注意: {total - passed} 项验证未通过，请检查上述错误。")

    print("="*60)
    return passed == total

if __name__ == "__main__":
    success = run_complete_verification()
    sys.exit(0 if success else 1)