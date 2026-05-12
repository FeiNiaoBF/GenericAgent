# Anki英语单词添加 SOP

> 触发词："记单词" + 单词列表
> 模型：`英语综合语料库`，12字段/3模板
> 前置：Anki运行中，AnkiConnect端口8765

## 关键前置
- 12字段：ID/Word/IPA-UK/Audio-UK/IPA-US/Audio-US/Meanings/Examples/Comparison/WordForms/Notes-Culture-Slang/Image
- ID：查当前最大ID+1，5位零填充(00010, 00011...)
- 释义：中英双语，英文在前中文在后
- Comparison：有则填无则空，不强求
- 推送：`addNote`逐个添加，失败重试1次仍失败则报主人

## 数据源
- **首选**：Free Dictionary API `https://api.dictionaryapi.dev/api/v2/entries/en/{word}` — 无需key，返回音标/释义/例句/词形/音频
- **备选**：Web搜索Oxford/Cambridge页面提取
- **中文释义**：唧翻译补充
- **音频URL**：直接用API返回的mp3链接，格式 `[sound:url]`

## 执行流程
1. **接收** — 从主人消息提取单词列表
2. **查词** — Free Dictionary API查每个词，失败则Web搜索补充
3. **最大ID** — `findNotes`查询当前笔记数，取最大ID+1
4. **组装** — 按12字段规范组装，Examples为普通句子，**禁止`{{c1::}}`填空语法**（模型非Cloze类型会报错）
5. **推送** — `addNote`逐个添加（仅填ID+Word+Audio+Comparison+WordForms+Notes等非HTML字段），成功后`updateNoteFields`补填Meanings/Examples等含HTML的字段
6. **验证** — `notesInfo`抽查2张，确认字段完整性
7. **报告** — 告诉主人添加了多少个

## 音频下载
- Anki媒体目录：`C:\Users\Yeekox\AppData\Roaming\Anki2\账户 1\collection.media`（注意是`账户 1`不是`User 1`）
- 文件名格式：`{word}-us-fd.mp3`
- URL格式：`https://api.dictionaryapi.dev/media/pronunciations/en/{word}-us.mp3`
- 下载后写入Audio-US字段：`[sound:{word}-us-fd.mp3]`

## 典型坑
1. **API返回404** → 该词不在Free Dictionary库中，改用Web搜索
2. **音频URL失效** → 跳过Audio字段，不阻塞添加
3. **ID冲突** → 每次添加前实时查最大ID，不用缓存值
4. **词形变化不全** → API只返回部分，缺的留空不瞎填
5. **addNote返回null** → 检查modelName拼写是否精确匹配`英语综合语料库`
6. **addNote报unknown reason** → HTML/声卡标签导致失败，改用**两步法**：先addNote只填ID+Word+Audio+Comparison+WordForms+Notes，成功后updateNoteFields补填Meanings/Examples等HTML字段
7. **Anki媒体路径** → 是`账户 1`不是`User 1`，先`os.listdir`确认profile名
