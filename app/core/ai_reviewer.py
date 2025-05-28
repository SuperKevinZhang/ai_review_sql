"""AI审查器"""

import json
import re
from typing import Dict, Any, Optional, List
import openai
import requests
from datetime import datetime

from app.models.llm_config import LLMProvider
from app.core.encryption import EncryptionService


class AIReviewer:
    """AI审查器，负责调用LLM进行SQL审查"""
    
    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.encryption_service = EncryptionService()
        self._setup_client()
    
    def _setup_client(self):
        """设置LLM客户端"""
        # 新版本的OpenAI库不需要全局设置，在调用时创建客户端
        pass
    
    def review_sql(self, sql_content: str, description: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        审查SQL语句
        
        Args:
            sql_content: SQL语句内容
            description: 业务描述
            schema_info: 数据库模式信息
            
        Returns:
            审查报告
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(sql_content, description, schema_info)
            # 打印提示词
            print("***************************提示词:")
            print(prompt)
            
            # 调用LLM
            print("***************************开始调用LLM...")
            response = self._call_llm(prompt)
            print("***************************LLM调用完成")
            
            # 解析响应
            review_result = self._parse_response(response)
            # 打印响应
            print("***************************响应:")
            print(review_result)
            
            return review_result
        
        except Exception as e:
            print(f"***************************AI审查过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"AI审查失败: {str(e)}",
                "overall_assessment": {
                    "status": "error",
                    "score": 0,
                    "summary": f"AI审查失败: {str(e)}"
                },
                "consistency": {"status": "error", "score": 0, "details": "", "suggestions": ""},
                "conventions": {"status": "error", "score": 0, "details": "", "suggestions": ""},
                "performance": {"status": "error", "score": 0, "details": "", "suggestions": ""},
                "security": {"status": "error", "score": 0, "details": "", "suggestions": ""},
                "readability": {"status": "error", "score": 0, "details": "", "suggestions": ""},
                "maintainability": {"status": "error", "score": 0, "details": "", "suggestions": ""},
                "optimized_sql": ""
            }
    
    def _build_prompt(self, sql_content: str, description: str, schema_info: Dict[str, Any]) -> str:
        """构建AI提示词"""
        
        # 格式化数据库模式信息
        schema_text = self._format_schema_info(schema_info)
        
        prompt = f"""
**角色:** 你是一个专业的SQL审查专家。你的任务是分析提供的SQL查询及其描述，结合数据库模式信息，生成全面的审查报告。

**上下文:**
1. **用户的SQL查询:**
```sql
{sql_content}
```

2. **用户对SQL意图的描述:**
"{description}"

3. **相关数据库模式:**
{schema_text}

**审查任务:**
请提供一个审查报告，涵盖以下方面。对于每个方面，请说明SQL是"优秀"、"良好"、"需要改进"还是"存在问题"。然后提供具体的细节、解释和可操作的改进建议。

**1. 一致性分析（SQL与描述的一致性）:**
- SQL查询是否准确实现了用户描述的功能？
- 如果不一致，请解释差异并建议修改SQL或描述。
- 如果意图描述为空，请根据SQL内容生成意图描述。

**2. SQL规范性和最佳实践:**
- 是否遵循命名约定（表、列、别名）。
- 是否正确使用JOIN。
- 格式化的可读性。
- 使用明确的列列表而不是`SELECT *`。
- 其他常见的SQL最佳实践。

**3. 性能分析:**
- 是否可能出现全表扫描。
- 是否有效使用索引进行JOIN、WHERE、ORDER BY子句。（参考模式的索引信息）
- 子查询或CTE的效率。
- 在WHERE子句中使用函数可能阻止索引使用。
- 任何其他潜在的性能瓶颈。
- 如果有益且缺失，建议具体的索引。

**4. 安全考虑:**
- 任何可能暗示SQL注入漏洞的模式（尽管这是静态分析，但可以标记可疑模式）。
- 查询是否请求过多数据或权限（例如，当只需要几列时，从包含敏感列的表中`SELECT *`）。

**5. 可读性和清晰度:**
- SQL是否易于理解？
- 是否有效使用别名？
- 复杂逻辑是否有足够的注释？
- 整体逻辑流程和复杂性。
- 是否有足够的注视

**6. 可维护性:**
- 将来修改这个SQL有多容易？
- 是否有应该参数化的硬编码值？
- 逻辑是否过于复杂或单一，建议分解？
- 查询中的冗余。

**输出格式:**
请用JSON格式结构化你的响应，包含以下字段：

```json
{{
    "overall_assessment": {{
        "status": "excellent|good|needs_improvement|has_issues",
        "score": 85,
        "summary": "总体评估摘要"
    }},
    "consistency": {{
        "status": "excellent|good|needs_improvement|has_issues",
        "score": 90,
        "details": "详细分析",
        "suggestions": "改进建议"
    }},
    "conventions": {{
        "status": "excellent|good|needs_improvement|has_issues",
        "score": 80,
        "details": "详细分析",
        "suggestions": "改进建议"
    }},
    "performance": {{
        "status": "excellent|good|needs_improvement|has_issues",
        "score": 75,
        "details": "详细分析",
        "suggestions": "改进建议"
    }},
    "security": {{
        "status": "excellent|good|needs_improvement|has_issues",
        "score": 95,
        "details": "详细分析",
        "suggestions": "改进建议"
    }},
    "readability": {{
        "status": "excellent|good|needs_improvement|has_issues",
        "score": 85,
        "details": "详细分析",
        "suggestions": "改进建议"
    }},
    "maintainability": {{
        "status": "excellent|good|needs_improvement|has_issues",
        "score": 80,
        "details": "详细分析",
        "suggestions": "改进建议"
    }},
    "optimized_sql": "优化后的SQL建议（如果需要），优化后SQL语句需要包含注释，注释需要解释优化后的SQL语句"
}}
```

请确保响应是有效的JSON格式。
"""
        return prompt
    
    def _format_schema_info(self, schema_info: Dict[str, Any]) -> str:
        """格式化数据库模式信息"""
        schema_text = ""
        
        # 处理SchemaExtractor返回的DDL格式
        if schema_info.get("tables"):
            schema_text += "**表结构:**\n"
            
            # 检查是否是DDL格式（字典形式）
            if isinstance(schema_info["tables"], dict):
                for table_name, table_info in schema_info["tables"].items():
                    schema_text += f"\n表名: {table_name}\n"
                    if table_info.get("ddl"):
                        schema_text += f"DDL:\n```sql\n{table_info['ddl']}\n```\n"
            else:
                # 处理旧格式（列表形式）
                for table in schema_info["tables"]:
                    schema_text += f"\n表名: {table['name']}\n"
                    schema_text += "列信息:\n"
                    for col in table.get("columns", []):
                        nullable = "可空" if col.get("is_nullable") else "非空"
                        comment = f" - {col.get('comment', '')}" if col.get('comment') else ""
                        schema_text += f"  - {col['name']}: {col['type']} ({nullable}){comment}\n"
                    
                    if table.get("indexes"):
                        schema_text += "索引:\n"
                        for idx in table["indexes"]:
                            unique = "唯一" if idx.get("is_unique") else "普通"
                            columns = ", ".join(idx.get("columns", []))
                            schema_text += f"  - {idx['name']}: {unique}索引 ({columns})\n"
                    
                    if table.get("primary_keys"):
                        pk_cols = ", ".join(table["primary_keys"])
                        schema_text += f"主键: {pk_cols}\n"
        
        # 格式化视图信息
        if schema_info.get("views"):
            schema_text += "\n**视图结构:**\n"
            for view in schema_info["views"]:
                schema_text += f"\n视图名: {view['name']}\n"
                if view.get("definition"):
                    schema_text += f"定义: {view['definition']}\n"
        
        return schema_text
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        provider = LLMProvider(self.llm_config["provider"])
        
        if provider in [LLMProvider.OPENAI, LLMProvider.DEEPSEEK]:
            return self._call_openai_compatible(prompt)
        elif provider == LLMProvider.OLLAMA:
            return self._call_ollama(prompt)
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")
    
    def _call_openai_compatible(self, prompt: str) -> str:
        """调用OpenAI兼容的API"""
        try:
            # 兼容新版本的openai库
            from openai import OpenAI
            
            # 解密API密钥
            api_key = self.encryption_service.decrypt_api_key(self.llm_config["api_key"])
            
            # 验证API密钥
            if not api_key or api_key.strip() == "":
                raise Exception("API密钥为空，请检查LLM配置")
            
            # 创建客户端，只传递必要的参数
            client_kwargs = {
                "api_key": api_key
            }
            
            # 只有当base_url不是默认值时才设置
            base_url = self.llm_config.get("base_url")
            if base_url and base_url != "https://api.openai.com/v1":
                client_kwargs["base_url"] = base_url
            
            client = OpenAI(**client_kwargs)
            
            response = client.chat.completions.create(
                model=self.llm_config["model_name"],
                messages=[
                    {"role": "system", "content": "你是一个专业的SQL审查专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config.get("temperature", 0.1),
                max_tokens=self.llm_config.get("max_tokens", 4000),
                top_p=self.llm_config.get("top_p", 1.0),
                frequency_penalty=self.llm_config.get("frequency_penalty", 0.0),
                presence_penalty=self.llm_config.get("presence_penalty", 0.0)
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            raise Exception(f"调用OpenAI兼容API失败: {str(e)}")
    
    def _call_ollama(self, prompt: str) -> str:
        """调用Ollama API"""
        try:
            url = f"{self.llm_config['base_url']}/api/generate"
            
            data = {
                "model": self.llm_config["model_name"],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.llm_config.get("temperature", 0.1),
                    "num_predict": self.llm_config.get("max_tokens", 4000)
                }
            }
            
            response = requests.post(
                url, 
                json=data, 
                timeout=self.llm_config.get("timeout", 60)
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        
        except Exception as e:
            raise Exception(f"调用Ollama API失败: {str(e)}")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 如果没有代码块，尝试直接解析
                json_str = response
            
            # 解析JSON
            result = json.loads(json_str)
            
            # 验证必要字段
            required_sections = ["overall_assessment", "consistency", "conventions", 
                               "performance", "security", "readability", "maintainability"]
            
            for section in required_sections:
                if section not in result:
                    result[section] = {
                        "status": "unknown",
                        "score": 0,
                        "details": "解析失败",
                        "suggestions": ""
                    }
            
            return result
        
        except json.JSONDecodeError as e:
            # 如果JSON解析失败，返回错误信息
            return {
                "error": f"解析AI响应失败: {str(e)}",
                "raw_response": response,
                "overall_assessment": {
                    "status": "error",
                    "score": 0,
                    "summary": "AI响应解析失败"
                }
            }
        
        except Exception as e:
            return {
                "error": f"处理AI响应时出错: {str(e)}",
                "overall_assessment": {
                    "status": "error",
                    "score": 0,
                    "summary": "处理失败"
                }
            } 