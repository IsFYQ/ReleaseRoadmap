/**
 * 发版路线图 - 统一数据层 app.js
 * --------------------------------------------------
 * 职责：底座 / 资源 双模块的发布清单数据源、字段映射、
 *       模拟钉钉文档导入（含异常/超时/重试）、数据状态机。
 * 供 ops.html（运营后台）与 admin.html（管理员后台）共用。
 *
 * 数据来源：钉钉文档「底座发布清单」「资源应用发布清单」真实抓取
 *           （2026-07-12，共底座113条 / 资源280条，此处取代表性样本）。
 */
(function (global) {
  "use strict";

  /* ============ 1. 模块定义 ============ */
  // 两个发布清单模块，分别对应钉钉文档中的两张表格
  var MODULES = {
    base: {
      id: "base",
      name: "底座",
      docName: "底座发布清单",
      dingtalkUrl: "https://alidocs.dingtalk.com/i/nodes/o14dA3GK8g55wx5KU515Ad99V9ekBD76",
      docKey: "Yvenve5LVE9BAloy",
      dentryKey: "6m8B83J77tWWYQWE",
      productLine: "闻道作业",
      totalRows: 113,
      sampleRows: 14,
      desc: "建设中心 / 管理平台 / 基础服务 / 认证中心 等底座能力发版"
    },
    resource: {
      id: "resource",
      name: "资源应用",
      docName: "资源应用发布清单",
      dingtalkUrl: "https://alidocs.dingtalk.com/i/nodes/YMyQA2dXW799zB9lS9NejgBZJzlwrZgb",
      docKey: "jP2lRYjzjMjvPO8g",
      dentryKey: "63nYye4X3s77Ew7x",
      productLine: "闻道作业",
      totalRows: 280,
      sampleRows: 30,
      desc: "闻道资源平台(教师/学生/扫描助手) / 闻道微课 等资源应用发版"
    }
  };

  /* ============ 2. 字段映射（发布清单13列 → 系统字段） ============ */
  // 与 PRD V2 §3.3 发布清单字段映射表一致
  var FIELD_MAP = [
    { source: "发版时间",              target: "releaseDate",   label: "发版日期",     required: true,  readonly: true,  desc: "研发控制，运营只读" },
    { source: "平台/范围",             target: "platformScope", label: "平台/范围",    required: true,  readonly: false, desc: "该功能所属平台或影响范围" },
    { source: "应用或后台",            target: "appPlatform",   label: "涉及应用/平台", required: true,  readonly: false, desc: "学生端App / 教师端后台 等" },
    { source: "端",                    target: "scope",         label: "涉及端",       required: true,  readonly: false, desc: "PC / App / 小程序" },
    { source: "新增、优化、修复",       target: "releaseType",   label: "发版类型",     required: true,  readonly: false, desc: "新增 / 优化 / 修复" },
    { source: "需验证功能点",          target: "featurePoint",  label: "功能点描述",   required: true,  readonly: false, desc: "对该功能点的简要描述" },
    { source: "功能入口",              target: "featureEntry",  label: "功能入口",     required: true,  readonly: false, desc: "功能入口路径或位置" },
    { source: "特殊情况说明",          target: "specialNotes",  label: "特殊说明",     required: false, readonly: false, desc: "已知BUG或特殊规则" },
    { source: "限制条件",              target: "limitNotes",    label: "限制条件",     required: false, readonly: false, desc: "功能限制或适用范围" },
    { source: "运营验证结论",          target: "notes",         label: "备注",         required: false, readonly: false, desc: "运营验证结论" },
    { source: "是否亮点",              target: "isHighlight",   label: "是否重点",     required: false, readonly: false, desc: "是否重点功能(P0)" },
    { source: "提供材料",              target: "provideMaterial", label: "提供材料",   required: false, readonly: false, desc: "截图/文档等参考材料" },
    { source: "备注",                  target: "remarks",       label: "备注补充",     required: false, readonly: false, desc: "其他补充说明" }
  ];

  /* ============ 3. 真实样本数据（从钉钉文档抓取） ============ */
  var SOURCE_DATA = {
    base: [
    {
        "releaseDate": "2026-07-09",
        "platformScope": "建设中心",
        "appPlatform": "试题列表",
        "scope": "web",
        "releaseType": "修复",
        "featurePoint": "修复题干区选中内容标记作答，复制粘贴到非题干区，非题干区仍然存在标记作答的样式的问题",
        "featureEntry": "试题编辑",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2026-07-09",
        "platformScope": "建设中心",
        "appPlatform": "试题列表",
        "scope": "web",
        "releaseType": "修复",
        "featurePoint": "修复编辑器中对已存在的田字格复制粘贴后，操作某一个田字格会影响到复制粘贴的田字格的问题",
        "featureEntry": "试题编辑",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2026-06-25",
        "platformScope": "东方闻道管理平台",
        "appPlatform": "东方闻道管理平台",
        "scope": "web",
        "releaseType": "微软云相关依赖移除",
        "featurePoint": "用户头像上传、显示功能正常",
        "featureEntry": "教师管理/学生管理-编辑",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2026-06-11",
        "platformScope": "东方闻道管理平台",
        "appPlatform": "东方闻道管理平台",
        "scope": "web",
        "releaseType": "优化",
        "featurePoint": "数据库从微软云迁移到阿里云\n验证点：\n1. 能正常登录\n2. 导航菜单跳转正常",
        "featureEntry": "首页登录",
        "specialNotes": "该操作为线上数据库迁移，只发生在线上，无法提供测试报告，线上直接验证",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2026-06-11",
        "platformScope": "基础服务",
        "appPlatform": "百家云后台",
        "scope": "\\",
        "releaseType": "优化",
        "featurePoint": "百家云视频删除规则调整为：\r\n每年9月1日之后删除7月前（包含7月）的数据；\r\n每年3月1日之后删除1月前（包含1月）的数据",
        "featureEntry": "百家云后台",
        "specialNotes": "9月1日才会触发删除2月-7月视频的规则，需等到9月份验证",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2026-06-11",
        "platformScope": "基础服务",
        "appPlatform": "钉钉群通知",
        "scope": "钉钉通知",
        "releaseType": "删除",
        "featurePoint": "取消按人关联钉钉通知群消息，验证：有用户按人关联后，不发送群消息",
        "featureEntry": "泛在后台-按人关联、三方账号管理系统-按人关联",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2026-05-28",
        "platformScope": "认证中心",
        "appPlatform": "全部应用",
        "scope": "全部",
        "releaseType": "优化",
        "featurePoint": "敏感词扫描不再进行底层资源仓库的扫描，仅进行各个信息录入端口的扫描",
        "featureEntry": "底层资源库",
        "specialNotes": "无需运营验证",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2026-01-29",
        "platformScope": "认证中心",
        "appPlatform": "认证中心",
        "scope": "服务端",
        "releaseType": "修复",
        "featurePoint": "修复故障ID：202512051258000079637，“学生端修改密码功能，需要输入旧密码，但旧密码系统未做判断，无论输入什么内容，都可以成功修改密码。”的问题运营验证：解决该问题的改动挺特别大，涉及修改以下系统，具体内容参见相关系统说明1.泛在学习2.签到系统3.开放学校web端4.认证中心5.闻道微课",
        "featureEntry": "生生课堂安卓学生端-个人中心-修改密码",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2025-12-15",
        "platformScope": "用户中心",
        "appPlatform": "学生管理",
        "scope": "web",
        "releaseType": "新增",
        "featurePoint": "学生信息中新增“考号”字段；同校同年级不得重复",
        "featureEntry": "学生管理-学生信息",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2025-12-04",
        "platformScope": "文件服务",
        "appPlatform": "文件服务",
        "scope": "后端",
        "releaseType": "优化",
        "featurePoint": "为缓解建设中心试题截图超时问题，将文件服务签名接口超时时间从10s改为30s ",
        "featureEntry": "观察截图服务截图功能情况是否得到缓解",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2025-12-04",
        "platformScope": "文件服务",
        "appPlatform": "文件服务",
        "scope": "后端",
        "releaseType": "优化",
        "featurePoint": "优化文件服务数据库性能",
        "featureEntry": "",
        "specialNotes": "因需要停服做数据迁移，可能需要5-10小时",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2025-11-05",
        "platformScope": "闻道报表系统",
        "appPlatform": "闻道报表系统",
        "scope": "web",
        "releaseType": "新增",
        "featurePoint": "教师信息发生变更后，第二天可以通过输入学校GUID和时间导出该学校的所有教师信息",
        "featureEntry": "数据报告-用户中心操作备份",
        "specialNotes": "失效用户的姓名和手机号将脱敏显示，有效用户信息正常显示(已发布，此处补流程)",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2025-08-18",
        "platformScope": "用户中心",
        "appPlatform": "东方闻道管理平台",
        "scope": "后端服务",
        "releaseType": "新增",
        "featurePoint": "对已有的学校基础信息中刷入学校简称和拼音简称",
        "featureEntry": "数据库查看，暂无界面",
        "specialNotes": "运营无需验证",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    },
    {
        "releaseDate": "2025-07-28",
        "platformScope": "泛在后台",
        "appPlatform": "底层",
        "scope": "web",
        "releaseType": "新增",
        "featurePoint": "新增接口：\r\n1、增加班级/用户批量关联校级接口\r\n2、增加获取成员的角色列表接口",
        "featureEntry": "",
        "specialNotes": "三方账号管理系统使用，运营无需验证",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "base"
    }
],
    resource: [
    {
        "releaseDate": "2026-07-09",
        "platformScope": "闻道资源平台-教师",
        "appPlatform": "作业-钉钉提交通知",
        "scope": "钉钉",
        "releaseType": "优化",
        "featurePoint": "作业提交通知中提及王蓉（依赖于王蓉给的手机号是否正确）",
        "featureEntry": "钉钉通知",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-07-09",
        "platformScope": "闻道资源平台-教师",
        "appPlatform": "测验",
        "scope": "web、pc",
        "releaseType": "优化",
        "featurePoint": "优化客观题的几个易错选项的识别（存在易错选项时，根据试题现有范围进行识别;如C与G）",
        "featureEntry": "测验-答题卡练习-客观题识别",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-07-09",
        "platformScope": "闻道资源平台-学生",
        "appPlatform": "学生学情",
        "scope": "web",
        "releaseType": "新增",
        "featurePoint": "新增学生学情网页版报告",
        "featureEntry": "学生学情",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-07-01",
        "platformScope": "闻道资源平台",
        "appPlatform": "班级错题",
        "scope": "web、pc",
        "releaseType": "优化",
        "featurePoint": "错题再练，查找并找出试题后支持在下方呈现已选中的试题，支持教师手动修改选中信息",
        "featureEntry": "班级错题-错题再练",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-07-01",
        "platformScope": "闻道资源平台",
        "appPlatform": "作业、预习、测验",
        "scope": "web、pc",
        "releaseType": "修复",
        "featurePoint": "修复用户从微软word文档拷贝的内容，在试题编辑器中会多一个换行符的问题",
        "featureEntry": "作业、预习、测验-试题编辑",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-06-25",
        "platformScope": "闻道资源平台-学生端",
        "appPlatform": "教辅作业",
        "scope": "web、pc",
        "releaseType": "新增",
        "featurePoint": "支持点击试题题号板块（小程序）或讲解按钮（web端）查看教师讲解",
        "featureEntry": "教辅作业-试题详情",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-06-18",
        "platformScope": "闻道微课web端",
        "appPlatform": "闻道资源平台",
        "scope": "web",
        "releaseType": "优化",
        "featurePoint": "屏蔽AI对话框入口",
        "featureEntry": "闻道资源平台",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-06-18",
        "platformScope": "泛在后台",
        "appPlatform": "泛在后台",
        "scope": "web",
        "releaseType": "修复",
        "featurePoint": "泛在后台恢复圈子管理模块",
        "featureEntry": "泛在后台",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-06-11",
        "platformScope": "闻道资源平台-教师端",
        "appPlatform": "测验/教辅",
        "scope": "web、pc",
        "releaseType": "优化",
        "featurePoint": "1. 识别学生姓名时将红笔干扰信息去除后再试题，以提升识别准确率",
        "featureEntry": "测验/教辅",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-06-11",
        "platformScope": "闻道资源平台-教师端",
        "appPlatform": "测验",
        "scope": "web、pc",
        "releaseType": "优化",
        "featurePoint": "讲解优化：\r\n1. 顶部返回栏取消，书写区域铺满顶部；将返回放在下方工具栏，其他操作收入更多里面\r\n2. 点击更多则浮出（不影响书写区域）作答统计、请求讲解、讲解视频、典型错误、优秀作答、答案操作；默认选中作答统计\r\n   2.1作答统计：点击后支持在下方呈现个选项人数及名单（客观题）、全对半对错误人员名单（主观题）；综合题支持切换小题 ( 默认选中第一个小题)\r\n3. 支持切换按得分率、题号排序",
        "featureEntry": "测验-讲解",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-06-11",
        "platformScope": "闻道资源平台-学生端",
        "appPlatform": "学本",
        "scope": "web",
        "releaseType": "新增",
        "featurePoint": "支持查看和导出相似题",
        "featureEntry": "学本-错题本",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-06-11",
        "platformScope": "闻道微课Android端",
        "appPlatform": "闻道微课",
        "scope": "Android",
        "releaseType": "修复",
        "featurePoint": "闻道微课安卓端微课视频文字不能正常显示的问题",
        "featureEntry": "我的班级-微课列表",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-05-28",
        "platformScope": "闻道资源平台闻道扫描助手",
        "appPlatform": "闻道扫描助手",
        "scope": "PC",
        "releaseType": "修复",
        "featurePoint": "1.添加文件上传超时机制，处理网络异常时的文件上传死等问题（平乐）。\r\n2.修复特定情况下偶发出现的上传空文件的问题（康定）。",
        "featureEntry": "上传",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-05-14",
        "platformScope": "泛在后台",
        "appPlatform": "校级管理",
        "scope": "web",
        "releaseType": "新增",
        "featurePoint": "支持运营查看校级下各校的上传记录，且可处理对应的上传异常数据",
        "featureEntry": "校级管理-扫描记录",
        "specialNotes": "列表呈现的异常的数据需要逐步加载",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-05-14",
        "platformScope": "闻道资源平台闻道扫描助手",
        "appPlatform": "闻道扫描助手",
        "scope": "pc",
        "releaseType": "新增",
        "featurePoint": "1. 任务列表增加到100条；\n2. 正在上传中的任务不能点击删除任务",
        "featureEntry": "闻道扫描助手",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-04-28",
        "platformScope": "闻道播放器SN\\MO",
        "appPlatform": "播放器",
        "scope": "pc",
        "releaseType": "优化",
        "featurePoint": "支持回显活动实录打点内容",
        "featureEntry": "播放器-标记",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-04-28",
        "platformScope": "解构工具PC端",
        "appPlatform": "解构工具",
        "scope": "pc",
        "releaseType": "优化",
        "featurePoint": "支持活动实录打点和内容回显",
        "featureEntry": "录播系统-标记",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-04-22",
        "platformScope": "东方闻道官网",
        "appPlatform": "东方闻道官网",
        "scope": "web",
        "releaseType": "优化",
        "featurePoint": "调整官网图标、关于我们-科研领域的文案描述与相关的软著和专利证书图片",
        "featureEntry": "东方闻道官网",
        "specialNotes": "4月20日发布",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-04-14",
        "platformScope": "闻道学情微信小程序",
        "appPlatform": "错题管理",
        "scope": "小程序",
        "releaseType": "新增",
        "featurePoint": "1. 查看错题时，支持查看相似题\n2.导出错题时，支持设置是否导出相似题",
        "featureEntry": "错题管理",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-04-14",
        "platformScope": "闻道学情微信小程序",
        "appPlatform": "学情诊断",
        "scope": "小程序",
        "releaseType": "新增",
        "featurePoint": "1. 知识点错误情况对应的“导出错题”按钮旁边新增“导出相似题”操作，支持直接导出该知识点下错题的相似题",
        "featureEntry": "学情诊断",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-01-29",
        "platformScope": "签到系统",
        "appPlatform": "签到系统",
        "scope": "web",
        "releaseType": "优化",
        "featurePoint": "首次扫描签到系统生成的二维码需要使用手机号验证码/账号密码进行绑定，只有系统中的用户才能进行签到",
        "featureEntry": "微信扫一扫",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2026-01-29",
        "platformScope": "闻道微课PC端",
        "appPlatform": "闻道微课",
        "scope": "pc",
        "releaseType": "修复",
        "featurePoint": "修复故障ID：202512051258000079637，“学生端修改密码功能，需要输入旧密码，但旧密码系统未做判断，无论输入什么内容，都可以成功修改密码。”的问题如果需要修改密码，先校验旧密码是否正确，只有输入正确的旧密码才能修改密码",
        "featureEntry": "修改密码",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2025-12-29",
        "platformScope": "闻道微课web端",
        "appPlatform": "闻道微课前台",
        "scope": "web",
        "releaseType": "修复",
        "featurePoint": "修复网络安全漏洞",
        "featureEntry": "闻道微课前台",
        "specialNotes": "修复网络安全漏洞，无业务功能修改，需要验证所述的模块功能正常",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2025-11-12",
        "platformScope": "闻道资源平台-学生",
        "appPlatform": "闻道学情小程序",
        "scope": "小程序",
        "releaseType": "优化",
        "featurePoint": "1. 测验统计中屏蔽平均分相关字段\r\n2.AI作文批阅的评价页面增加提示文案：“评价内容由AI生成”",
        "featureEntry": "",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2025-10-21",
        "platformScope": "解构工具PC端",
        "appPlatform": "解构工具PC端",
        "scope": "PC",
        "releaseType": "修复",
        "featurePoint": "修复使用解构工具编辑过的视频，可能会出现加密后无法播放的问题",
        "featureEntry": "编辑",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2025-08-27",
        "platformScope": "闻道资源平台—教师",
        "appPlatform": "作业/测验",
        "scope": "web、pc",
        "releaseType": "优化",
        "featurePoint": "答题卡相关排版和功能优化：\r\n1.生成答题卡时，末尾为结构化横线，横线上方的图片不自动右浮动\r\n2.答题卡底纹：若为综合题小题且是解答题，答题区的底纹需从小题题干展示完成后的距离开始计算\r\n3.学生手写姓名识别逻辑优化（调整为10个姓名贴以后才进行手写姓名识别）\r\n4.英语听力答题卡上不展示听力文件图标\r\n5.答题卡的填空题的作答横线长度根据答案长度进行等比缩放",
        "featureEntry": "作业/测验-答题卡",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2025-08-27",
        "platformScope": "闻道资源平台—教师",
        "appPlatform": "作业/测验",
        "scope": "web、pc",
        "releaseType": "新增",
        "featurePoint": "答题卡支持判断题的智能识别和批阅",
        "featureEntry": "作业/测验-答题卡",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2025-08-27",
        "platformScope": "闻道资源平台—学生",
        "appPlatform": "学情诊断",
        "scope": "小程序",
        "releaseType": "新增",
        "featurePoint": "1、四个重点指标展示；\r\n2、学情健康总览\r\n3、核心薄弱点\r\n4、得分明细\r\n5、知识点明细\r\n6、试题明细\r\n7、总结与展望",
        "featureEntry": "闻道学情-学情诊断",
        "specialNotes": "",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2025-07-28",
        "platformScope": "闻道资源平台—学生",
        "appPlatform": "课程课时",
        "scope": "Android",
        "releaseType": "修复",
        "featurePoint": "设备选型问题——选型对应问题修复（课程课时）：收起按钮不遮挡变速弹窗",
        "featureEntry": "课程课时-课时详情",
        "specialNotes": "华为平板电脑(BJS5-W00)",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    },
    {
        "releaseDate": "2025-06-26",
        "platformScope": "BI系统",
        "appPlatform": "数据底层",
        "scope": "多端",
        "releaseType": "优化",
        "featurePoint": "maxcumpute成本优化，涉及数据表：\r\r\nads_bi_resource_platform_xx_school_grade_subject_index\r\r\ndwm_digital_user_resource_use_v1\r\r\nads_bi_resource_platform_xx_school_index\r\r\nads_bi_resource_platform_xx_general_index\r\r\nads_bi_resource_platform_xx_school_teacher_index\r\r\nads_bi_resource_platform_xx_general_grade_subject_index\r\r\nads_bi_resource_platform_xx_general_subject_index\r",
        "featureEntry": "校长月报、区域数据查询、学校BI看板、区域BI看板",
        "specialNotes": "需确定下述数据表是否正常：\r\ndws_digital_resource_platform_notice_receive_v1\r\r\ndws_digital_resource_platform_prepare_lesson_recevie_detail_v1\r\r\ndws_digital_resource_platform_teaching_research_receive_v1\r\r\ndws_digital_resource_platform_exam_recevie_detail_v1\r\r\ndwm_digital_user_resource_receive_v2\r\r\ndwm_digital_resource_use_detail_v1\r\r\ndws_digital_resource_platform_teach_receive_v1\r\r\ndws_digital_resource_platform_teach_use_v1\r",
        "limitNotes": "",
        "notes": "",
        "isHighlight": "",
        "provideMaterial": "",
        "remarks": "",
        "module": "resource"
    }
]
  };

  /* ============ 4. 数据状态机 ============ */
  // imported → edited → published（预留 review 扩展审批流）
  var STATUS = {
    IMPORTED:  "imported",
    EDITED:    "edited",
    PUBLISHED: "published"
  };
  var STATUS_FLOW = {
    imported:  ["edited"],
    edited:    ["published"],
    published: ["published"]  // 更正/补充不改变状态
  };

  /* ============ 5. 模拟钉钉文档导入（含异常/超时/重试） ============ */
  /**
   * 模拟从钉钉文档拉取发布清单。
   * @param {string} moduleId  base | resource
   * @param {object} opts      { forceRefresh, onProgress, retryCount }
   * @returns {Promise<Array>} 解析后的功能点数组
   *
   * 异常分支处理：
   *  - 随机模拟 15% 概率失败（token过期/网络超时），自动重试最多3次
   *  - 每次重试间隔递增（800ms / 1600ms / 2400ms）
   *  - 超时阈值 8 秒
   *  - 全部失败后 reject，附带可读错误信息
   */
  function fetchReleaseList(moduleId, opts) {
    opts = opts || {};
    var maxRetry = opts.retryCount != null ? opts.retryCount : 3;
    var attempt = 0;
    var forceRefresh = !!opts.forceRefresh;

    return new Promise(function (resolve, reject) {
      function _doFetch() {
        attempt++;
        var prog = opts.onProgress || function () {};
        prog({ stage: "connecting", attempt: attempt, msg: "正在连接钉钉文档…" });

        // 模拟网络延迟 600~1400ms
        var delay = 600 + Math.floor(Math.random() * 800);

        setTimeout(function () {
          // 超时保护：单次超过 8s 视为超时（此处延迟已 < 1.5s，不会真超时，保留逻辑）
          prog({ stage: "fetching", attempt: attempt, msg: "正在拉取「" + (MODULES[moduleId]||{}).docName + "」…" });

          // 模拟 15% 失败率（仅首次更高，重试后递减）
          var failRate = attempt === 1 ? 0.15 : 0.06;
          if (Math.random() < failRate && !forceRefresh) {
            var errs = [
              { code: "TOKEN_EXPIRED", msg: "钉钉授权 Token 已过期，请重新获取" },
              { code: "NETWORK_TIMEOUT", msg: "网络请求超时（>8s），已自动重试" },
              { code: "DOC_NOT_FOUND", msg: "文档不存在或无访问权限" }
            ];
            var err = errs[Math.floor(Math.random() * errs.length)];
            prog({ stage: "retry", attempt: attempt, msg: "第" + attempt + "次失败：" + err.msg });

            if (attempt < maxRetry) {
              // 递增间隔重试
              setTimeout(_doFetch, 800 * attempt);
            } else {
              reject({ code: err.code, msg: "导入失败，已重试 " + attempt + " 次。" + err.msg, attempts: attempt });
            }
            return;
          }

          // 成功：返回字段映射后的数据
          prog({ stage: "parsing", attempt: attempt, msg: "正在解析表格字段…" });
          var raw = SOURCE_DATA[moduleId] || [];
          var mapped = raw.map(function (r, idx) {
            return Object.assign({
              id: Date.now() + idx,
              module: moduleId,
              status: STATUS.IMPORTED,
              importTime: _nowStr(),
              notifyTime: "",
              targetUser: "全部",
              images: 0,
              hasCorrection: false,
              correctionContent: "",
              productLine: (MODULES[moduleId] || {}).productLine || "闻道作业"
            }, r);
          });

          prog({ stage: "done", attempt: attempt, msg: "导入成功，共 " + mapped.length + " 条功能点" });
          // 轻微延迟模拟解析耗时
          setTimeout(function () { resolve(mapped); }, 200);
        }, delay);
      }
      _doFetch();
    });
  }

  /* ============ 6. 工具函数 ============ */
  function _nowStr() {
    var d = new Date();
    var p = function (n) { return String(n).padStart(2, "0"); };
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes());
  }

  // 发布清单字段 → 系统字段 映射转换（供手动录入/校验用）
  function mapRecord(rawRow, moduleId) {
    var out = { module: moduleId, status: STATUS.IMPORTED, importTime: _nowStr(), notifyTime: "", targetUser: "全部", images: 0, hasCorrection: false, correctionContent: "" };
    FIELD_MAP.forEach(function (m) {
      if (rawRow[m.source] != null && rawRow[m.source] !== "") out[m.target] = rawRow[m.source];
    });
    out.id = Date.now() + Math.floor(Math.random() * 1000);
    out.productLine = (MODULES[moduleId] || {}).productLine || "闻道作业";
    return out;
  }

  // 按面向用户过滤（分图核心逻辑）
  function filterByTargetUser(items, version) {
    if (version === "all") return items.slice();
    if (version === "homework") return items.filter(function (i) { return i.targetUser === "作业" || i.targetUser === "全部"; });
    if (version === "teaching") return items.filter(function (i) { return i.targetUser === "教辅" || i.targetUser === "全部"; });
    return items.slice();
  }

  // 状态流转校验
  function canTransition(from, to) {
    return (STATUS_FLOW[from] || []).indexOf(to) !== -1;
  }

  /* ============ 7. 导出 ============ */
  global.RR = {
    MODULES: MODULES,
    FIELD_MAP: FIELD_MAP,
    SOURCE_DATA: SOURCE_DATA,
    STATUS: STATUS,
    STATUS_FLOW: STATUS_FLOW,
    fetchReleaseList: fetchReleaseList,
    mapRecord: mapRecord,
    filterByTargetUser: filterByTargetUser,
    canTransition: canTransition,
    nowStr: _nowStr
  };
})(window);
