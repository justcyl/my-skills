# Lark Slides Technical Notes

Use this file only when actually building or debugging a Feishu/Lark paper deck.

## Workspace

Use a temporary workspace under the current thread, for example:

```bash
mkdir -p work/paper-to-ppt/raw work/paper-to-ppt/media work/paper-to-ppt/slides
```

Save fetched document JSON, downloaded images, and generated slide XML there. Do not create a persistent database or topic manifest unless the user explicitly asks.

## Find And Read Source Docs

Prefer the newer `drive +search` if available in the installed `lark-cli`. If it is not available, use `docs +search`.

```bash
lark-cli docs +search --query "skill 论文" --page-size 20 --format json
```

For any reader document:

```bash
lark-cli docs +fetch --api-version v2 --doc "<doc-or-wiki-token>" --scope outline --max-depth 3 --format json
```

Then fetch only what is needed:

```bash
lark-cli docs +fetch --api-version v2 --doc "<token>" \
  --scope keyword \
  --keyword "核心问题|作者答案|关键想法|主要结果|方法|实验|局限|结论|贡献" \
  --context-after 1 \
  --doc-format markdown \
  --format json
```

Fetch XML when images are needed:

```bash
lark-cli docs +fetch --api-version v2 --doc "<token>" --doc-format xml --format json
```

Images usually appear as:

```xml
<img name="fig2_pipeline.png" caption="..." href="https://..." src="..."/>
```

If `href` exists, download it directly to `work/paper-to-ppt/media/`. If there is no usable URL, use the document media commands from the `lark` skill.

## Choose Images

For a useful paper deck, use a few images well rather than many images weakly. A slide image should answer one of these:

- What is the task/problem?
- What is the method mechanism?
- What evidence supports the central claim?
- What diagnosis or ablation explains why it works?
- What case or failure reveals the limitation?

Avoid decorative images and dense tables that cannot be read on a slide. If a table is essential but too dense, turn it into one conclusion plus a cropped or simplified visual.

## Create Slides

Use 16:9 SML, typically 960 x 540.

For decks of 10 pages or fewer, `slides +create --slides` is simplest and supports local image placeholders:

```bash
lark-cli slides +create --as user \
  --title "Deck Title" \
  --slides "$(cat work/paper-to-ppt/slides/slides.json)"
```

Image paths in slide XML must be relative to the command CWD and inside that CWD:

```xml
<img src="@./media/figure.png" topLeftX="80" topLeftY="120" width="520" height="300"/>
```

Do not put HTTP(S) URLs directly in `<img src="...">`; Feishu Slides will usually render them as broken images. Download web/doc images locally first and let `slides +create` upload them.

For more than 10 pages:

1. Create an empty presentation with `slides +create --title`.
2. Upload each image with `slides +media-upload`.
3. Add pages with `slides xml_presentation.slide create`.

## Minimal Slide XML

```xml
<slide xmlns="http://www.larkoffice.com/sml/2.0">
  <style>
    <fill><fillColor color="rgb(248, 247, 243)"/></fill>
  </style>
  <data>
    <shape type="text" topLeftX="52" topLeftY="36" width="820" height="44">
      <content textType="headline" fontSize="28" color="rgb(35,38,43)">
        <p><strong>Slide title</strong></p>
      </content>
    </shape>
    <img src="@./media/figure.png" topLeftX="64" topLeftY="116" width="520" height="300"/>
    <shape type="text" topLeftX="620" topLeftY="124" width="270" height="210">
      <content textType="body" fontSize="18" color="rgb(47,52,58)">
        <ul>
          <li><p>What this figure proves.</p></li>
          <li><p>Why it matters for the story.</p></li>
        </ul>
      </content>
    </shape>
  </data>
</slide>
```

Escape XML text (`&`, `<`, `>`, `"`) before writing slide XML.

## Layout Checks

Before creating the deck:

```bash
lark-cli slides +create --as user --title "Deck Title" \
  --slides "$(cat slides/slides.json)" \
  --dry-run
```

After creating the deck:

```bash
lark-cli slides xml_presentations get --as user \
  --params '{"xml_presentation_id":"<presentation-id>"}' \
  --format json > work/paper-to-ppt/slides/created-presentation.json

jq -r '.data.xml_presentation.content' work/paper-to-ppt/slides/created-presentation.json \
  > work/paper-to-ppt/slides/created-presentation.xml

rg -o '<slide' work/paper-to-ppt/slides/created-presentation.xml | wc -l
rg -o '<img ' work/paper-to-ppt/slides/created-presentation.xml | wc -l
rg '@\./media' work/paper-to-ppt/slides/created-presentation.xml
```

The final `rg` should return no matches. If it still finds `@./media`, the local image upload/replacement failed.

If the installed CLI supports exporting Slides, export and visually inspect the result. If not, state that only XML structure was checked.

## Final Response

Report:

- Slides title and Feishu URL.
- Source documents/papers used.
- Page count and image count.
- The main story spine in one sentence.
- Checks completed and any checks not possible.
