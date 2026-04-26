# skill name

critic_review

## purpose

对完整增长方案进行 Reflection，识别 badcase、原因和修复动作，形成迭代闭环。

## input

- full workflow output
- rag context
- metrics and experiment definitions

## output

- score summary
- main issues
- badcase risks
- root cause analysis
- remediation actions
- revised plan summary
- next iteration suggestions

## related agent

Critic Agent

## evaluation criteria

- 是否指出可执行问题而不是泛泛而谈
- 是否把问题绑定到漏斗环节和指标
- 是否给出可落地修复动作
- 是否形成下一轮迭代方向

## example

输入：A/B 测试只有实验名称，没有成功标准

输出：指出实验不可执行，要求补充实验组、对照组、核心指标、成功标准和验证方式。
