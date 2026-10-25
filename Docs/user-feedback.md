# User feedback

## Source

- Message date: 2026-10-24.
- The user repeated the feedback block twice in one message.
- The duplicate is removed here. The wording is kept.
- The current implementation is in `filtering_log_viewer.html`.
- The plan is in `Docs/change-plan.md`.

## 1. Row fill and legend background

> цвет заливки отличается от фона меток легенды (не путать с границей
> легенды - она темнее фона)

### Analysis

The viewer has two color sets.

- Summary chips use `--blocked`, `--allowed`, `--modified`, and
  `--cosmetic`. These are the saturated status colors.
- Table rows use `--row-blocked`, `--row-allowed`, `--row-modified`, and
  `--row-cosmetic`. These are pale tints.
- The chip border uses `--blocked-accent` and similar tokens. The border
  is darker than the chip background.

The user sees the summary chips as the legend. The row fill does not
match the chip background.

### Suspected cause

Two token sets describe one status. The table rewrite added the pale row
tints but did not update the summary chips.

### Acceptance

- One token set defines the status background.
- The row fill and the legend marker background are equal.
- The legend border stays darker than the marker background.
- The text keeps at least 4.5:1 contrast.

### User answer

The legend is above the search. It is the colored markers with a
border. The reference color is the marker background without the
border.

## 2. App and Process duplicate

> App и Process - это одно и тоже, просто по-разному написано. Убери тот
> App который слева после времени, а Process переименуй в App - там и
> процессы windows, и mac, и Android выводим. Для Android не всегда
> красивое имя приложения видно, но package_name тут сойдёт. Я бы даже
> упростил до package_name, .exe и программы как в макоси принято.

### Analysis

The table has two related columns.

- `App` is a colored badge with the app initial.
- `Process` is the friendly app name from `appName()`.

Both use the same `record.app` value. The user wants one App column.

The viewer parses Android logs. The payload has `packageName`. It has no
Windows process name and no macOS app name. The parser must keep the raw
value for the App column.

### Suspected cause

The table design kept the old app badge and added a Process column. Both
show the same source value.

### Acceptance

- Remove the App badge column after Time.
- Rename Process to App.
- Show the raw value:
  - Android: `package_name`.
  - Windows: process name with `.exe`.
  - macOS: application name.
- Do not substitute a friendly name in this column.
- The friendly name may stay in the details.
- The App column is hideable.
- Sorting uses the raw App value.

### Open question

Where do Windows and macOS values come from in the current log format?

### User answer

The Android log has only `packageName`.
The user supplied a Windows log with a different format.
Its fields are recorded in `Docs/log-samples.md`.
The parser will be extended later.
Many fields can have different names and the same meaning.

## 3. Column visibility

> Все колонки, кроме Time и URL сделай скрываемыми. Вместо кнопки или в
> дополнение можно сделать открытие списка столбцов по правой кнопке на
> заголовке таблицы.

### Analysis

The current `Columns` menu only shows Source and Process. The details
panel auto-hides App, Filter, and Method. The user wants user-controlled
visibility for all columns except Time and URL.

### Suspected cause

The visibility model was limited to the two optional columns. The
details auto-hide was hard-coded.

### Acceptance

- Time and URL are always visible.
- App, Type, Rule, Method, Filter, Source, and any other optional column
  can be hidden.
- The `Columns` button and a right-click on the header open the same
  menu.
- The menu opens at the pointer for a right-click.
- Visibility persists.
- The details auto-hide still applies.
- A column hidden by the user does not return when details close.
- A reset action restores the default set.

### User answer

All columns except Time and URL are hideable.
The right-click menu is accepted.
The details auto-hide and the user choice are independent.
Details hide only their own columns. The user choice is separate.

## 4. Column borders and resize affordance

> Границы столбцов может видимыми в заголовке сделать? Непонятно, что их
> можно растягивать.

### Analysis

The header has no vertical separators. The resize handle is a 7 px
transparent strip at the right edge. It becomes visible only on hover.
The user cannot see where a column ends.

### Suspected cause

The header uses only a bottom border. The resizer has no resting state.

### Acceptance

- Header cells have visible vertical separators.
- The separator is darker than the header background.
- The resize area is at least 9 px wide.
- The cursor changes to `col-resize` at the boundary.
- A tooltip says "Drag to resize".
- The separator becomes the accent color on hover.

### User answer

The user clicked the header and nothing happened.
The hit area must be larger and visible.

## 5. Double-click reset and keyboard resize

> Двойной клик по ручке сбрасывает колонку. Клавиатура: ← и → на ручке.
> это не понял. Кликал - ничего не поменялось.

### Analysis

The reset only works on the 7 px handle. A click on the header word sorts.
The user clicked the word, not the handle. The keyboard path requires
focus on the handle, which has no visible focus target.

### Suspected cause

The handle is small and invisible. The reset is not discoverable.

The user clicked the handle itself. The cursor changed to the resize
cursor. The double-click still did nothing.

Likely cause: `endColumnDrag` re-renders the header on pointerup.
The second click lands on a new handle element, so the browser does not
emit `dblclick`.

### Acceptance

- Double-click on the visible separator resets the column.
- The reset is tested.
- The handle is focusable and has a visible focus ring.
- `Left` and `Right` resize the column when the handle has focus.
- A tooltip explains both actions.

### User answer

The user clicked the header, not the 7 px handle.
The reset must be reachable from the visible boundary.
The keyboard path must be discoverable.

## 6. Sorting by the whole header cell

> Сортировка по клику на заголовок. Есть asc/desc и индикатор.
> только по слову работает. Может как в Проводнике сделать - по ячейке
> шапки таблицы?

### Analysis

The sort button is inside the header cell. It covers only the label. The
padding and the area near the resizer do not sort.

### Suspected cause

The click handler is on the button, not on the header cell.

### Acceptance

- A click anywhere in the header cell sorts, except on the resize handle.
- The resize handle does not sort.
- The whole cell shows a pointer cursor.
- The sort arrow remains.
- Keyboard sorting still works.
- The header cell has a visible hover state.

### User answer

The user focuses a row in Chrome.
The header cell must sort on a click anywhere outside the resizer.

## 7. Cell tooltip

> Подсказка на ячейке, не на строке. Показывается только при обрезке
> текста.
> перепроверь. В Type при обрезке "Other, Ajax" до "Other, Aj..." не
> появилась. У Source и Process тоже не вижу. Везде одинаково просто
> добавь.

### Analysis

The current tooltip uses pointer events and checks for a `.truncate`
child. It does not work for the reported cells.

Possible causes:

- The pointer enters a child element, and the event guard skips the
  cell.
- The truncation check uses the wrong element.
- The tooltip is hidden by a later event.
- Source and Process were hidden when the user tested them.

### Suspected cause

The tooltip logic is not uniform across cell types. The truncation
detection is fragile.

### Acceptance

- Every cell uses the same tooltip path.
- The tooltip appears only when the text is cut.
- Type, Source, Process, URL, Rule, Filter, and App are covered.
- The tooltip text is the full cell value.
- A test checks each column at a narrow width.
- The tooltip hides on scroll, resize, click, and overlay open.

### User answer

The `+N` popup must stay open while the pointer is over it.
The user must be able to select the text.
The popup closes when the pointer leaves the cell and the popup.

All popups use one component.
The maximum width is 30% of the screen.
The popup opens below the cell.
The text can be selected and copied.
The hide delay is about 250 ms.

## 8. Ctrl-F

> Ctrl-F ставит фокус в поиск.
> не сработало

### Analysis

The viewer has a document keydown handler for `Ctrl-F` and `Cmd-F`.
Possible causes:

- The browser opens its own find dialog before the page handles the key.
- The search field is disabled or behind an overlay.
- The user pressed the shortcut while a drawer or overlay was open.
- The page handler returns early because the hide modal is open.

### Suspected cause

The handler does not always prevent the browser shortcut. It also skips
some overlay states.

### Acceptance

- `Ctrl-F` focuses the search field when a log is loaded.
- The browser find does not open.
- The shortcut closes the columns menu.
- The shortcut closes a drawer or an overlay that blocks the search.
- The shortcut is tested in Chromium, Firefox, and Safari if possible.
- `/` works as a fallback shortcut.
- The search field shows a shortcut hint.

### User answer

The user uses Chrome and focuses a row.
The handler must catch the key before the browser.
A CodeMirror-style capture listener is acceptable.

The implementation uses a capture listener.
It closes the columns menu, the filters drawer, and phone details.
It focuses and selects the search field.
The Chrome check passed.

## 9. Tracking Protection for modified meta

> Там где modified meta - применён модуль Tracking Protection. В Filter
> просто пиши название модуля Tracking Protection, а в Rule - Cosmetic /
> Stealth (короткое название Tracking Protection) список опций индицируй
> xN и выводи при наведении (например Stealth mode опции - Do Not Track,
> Remove X-Client-Data). Если и Cosmetic и Stealth - красить строку
> желтым как HTML, как ниже в куске json

The user supplied this JSON fragment:

```json
"modifiedMetaReason": [
    "STEALTHMODE"
  ],
  "modifiedContentReasons": [
    "COSMETIC_RULE"
  ],
```

The user corrected the count label: use `+N`, not `xN`.

### Analysis

The current status mapping does this:

- `STEALTHMODE` gives `META_MODIFIED`.
- `COSMETIC_RULE` gives `MODIFIED`.
- `META_MODIFIED` uses the gray `modified` row.
- `MODIFIED` uses the yellow `cosmetic` row.
- The Filter column shows filter list names.
- The Rule column shows the first applied rule.

The user wants a module view:

- Filter column: `Tracking Protection` for meta modified rows.
- Filter column: `Cosmetic` for content-only rows.
- Rule column: `Stealth`, `Cosmetic`, or both.
- A count `+N` for the option list.
- Hover shows the options.
- The popup stays open while the pointer is over it.
- Both Cosmetic and Stealth: yellow row.

### Suspected cause

The viewer exposes raw filter lists and rules. It does not expose the
Tracking Protection module or its option list.

### Acceptance

- A `META_MODIFIED` row with stealth options shows
  `Filter = Tracking Protection`.
- The Rule cell shows `Stealth` and `+N`.
- The tooltip lists the stealth options.
- The popup is selectable and hoverable.
- A row with both cosmetic and stealth shows `Cosmetic / Stealth` and
  is yellow.
- A row with only cosmetic content shows `Filter = Cosmetic` and
  `Rule = Cosmetic`.
- A row with only stealth shows `Filter = Tracking Protection` and
  `Rule = Stealth`.
- The details panel lists the same options.
- The mapping is tested with the JSON fragment above.

### Open question

What are the exact short names and option labels for all
`modifiedMetaReason` and `modifiedContentReasons` values?

## 10. Unclear labels

> Meta Modified Proxy Request и Content Modified Proxy Request
> это непонятно откуда ты взял

### Analysis

The labels come from the new Android log format.
`recent_activity1.json` contains these event names:

- `metaModifiedProxyRequest` - 2 807 records.
- `contentModifiedProxyRequest` - 114 records.

`eventLabel()` has no case for these names.
It calls `humanizeEvent()`.
`metaModifiedProxyRequest` becomes `Meta Modified Proxy Request`.
`contentModifiedProxyRequest` becomes `Content Modified Proxy Request`.

The labels were not invented. They are a direct result of the unknown
event names.

The user saw them after importing `recent_activity1.json`.
The app changed the log event structure.

### Suspected cause

The viewer only knows the old event names.
The new names fall through to the humanizer.

### Acceptance

- Map `metaModifiedProxyRequest` and
  `contentModifiedProxyRequest` to the normal proxy event label.
- Do not show the raw event name in the table.
- Keep the status in the status field, not in the event name.
- Test with `Docs/samples/android-new.json`.

## 11. Content types became Other

> Сломалось определение типов контента - всё стало Other. Может из-за
> того что появились ранее отсутствовавшие Proxy Request в коде?

### Analysis

There are two separate cases.

`recent_activity3.json` has no `resourceTypes` at all.
All 165 records are connections.
The viewer now shows `Connection` for them.
`Other` was the old fallback for that file.
The user's note about a connections-only log explains this case.

`recent_activity1.json` uses the new event names.
It has 3 407 records with `resourceTypes`.
The viewer ignores them because `contentTypes()` only reads resource
types for `processedProxyRequest`.
`eventGroup()` also returns `other` for the new proxy events.

`Proxy request` is an event label. It does not change content types.

### Suspected cause

The new Android event names are not mapped.
The content type data exists but is not read.

### Acceptance

- Map every new proxy event to the web event group.
- Read `resourceTypes` for every new proxy event.
- Do not show `Other` when a known resource type exists.
- Use `Connection` for a connections-only record with no resource type.
- Keep `Other` only for a web request with no known resource type.
- Add `Docs/samples/android-new.json` as a regression fixture.
- Add `Docs/samples/android-connections.json` as a regression fixture.

### Open question

Confirm the new event names with the product code or a field
dictionary.

## 12. Hide list draft and Apply

> Hide Filter применяется и сохраняется сразу после импорта, но до
> нажатия Apply. Можно сделать фичей - до Apply не сохранять, но
> добавить пометку, что это типа интерактивного режима с предпросмотром
> изменений. При закрытии не сохранять. Когда нечего сохранять и после
> сброса - Apply должна быть серой. Сброс сохраняет пустой фильтр и
> сереет Apply.

### Analysis

The current modal edits live state. Import, add, remove, toggle, and
reset call `saveHideList()` immediately. `Apply` only closes the modal.

The user wants a draft model:

- Changes preview in the log.
- Changes are not saved before Apply.
- Closing without Apply discards them.
- Apply is gray when the draft equals the saved state.
- Reset clears the fields and activates Apply if it is disabled.
- Reset does not save immediately.

### User answer

Reset clears the fields.
It activates the save button when the button is disabled.
The user must see that saving is still needed.

The user suggests renaming `Apply` to `Save`.
The rest of the draft model is accepted.

### Suspected cause

The modal was built as a live editor. Apply is only a close button.

### Acceptance

- The modal has a saved state and a draft state.
- Import and edits change the draft and the live preview.
- Close or Cancel discards the draft and restores the saved state.
- `Save` writes the draft to storage and closes.
- `Save` is disabled when the draft equals the saved state.
- `Save` is disabled after a successful save.
- Reset clears the draft and enables `Save`.
- Reset does not write storage.
- The modal shows "Preview" or "Unsaved changes".
- The sidebar switch follows the same draft rule, or is clearly
  separate.
- Import is part of the draft.

## 13. Rules with domain lists

> Новый запрос - есть правила фильтрации с перечислением доменов.
> Например:
>
> ```
> /js/ads/admaven.js$domain=mangabats.com|mangakakalot.gg|mangakakalove.com|manganato.gg|natomanga.com|nelomanga.net
> standard-freeholder.com,recorder.ca,thewhig.com##.pmd-ad-container
> ```
>
> таки правила с $domain=*|*|* и domain1.com,domain2.com,domainN.com
> нужно обрезать вот так
>
> ```
> /js/ads/admaven.js$domain=mangabats.com|...
> standard-freeholder.com,...##.pmd-ad-container
> ```
>
> и показывать индикатор +N, и считать такие строки обрезанными - т.к.
> при наведении на ячейку правила показывать подсказку с исходным
> правилом. Если более 7 строк - применять серединное обрезание. В
> деталях если надо увидим или скопируем полное правило.

### Analysis

The rule column shows the first applied rule.
Long domain lists are cut by the browser at the cell edge.
The user wants a compact domain list with a count.

The two forms are:

- `$domain=` lists with `|`.
- Cosmetic domain lists with `,`.

The compact form keeps the rule start, the first domain, and `...`.
The cell shows `+N` for the hidden domains.
The cell counts as truncated even when the compact text fits.
Hovering the cell shows the full original rule.
The details panel shows and copies the full rule.

If a rule has more than 7 domains, the user wants middle
truncation. The exact shape is still open.

### Suspected cause

The rule cell is a single-line browser ellipsis.
It has no domain-list formatter.

### Acceptance

- `/js/ads/admaven.js$domain=mangabats.com|...` for a `$domain` list.
- `standard-freeholder.com,...##.pmd-ad-container` for a cosmetic
  list.
- `+N` shows the number of hidden domains.
- The cell is treated as truncated.
- Hover shows the full original rule.
- The details panel shows the full rule and copies it.
- A list with more than 7 domains uses middle truncation.
- The formatter keeps other modifiers after the domain list.
- The formatter handles `~domain` exceptions.
- The existing applied-rule count is not confused with the domain
  count.
- The `+N` popup is hoverable and selectable.

### User answer

Use the middle form only when a list has more than 15 domains.
Keep the first 3 and the last 3.
`+N` is the number of hidden domains.
The `+10` in the long example was arbitrary. The correct value
for 20 domains is `+14`.
The applied-rule count and the domain count are separate.
The domain count uses `+N`.
The applied-rule count uses `+N rules`.

## 14. Details on a narrow or tablet screen

> ты про оверлей какого окна? Если деталей - то у него оверлей не
> нужен. Если экран планшетный, чтобы удобнее было выбирать.

### Analysis

The current viewer uses a modal overlay for details below 1200 px.
The overlay has a backdrop and makes the table inert.
The user says details do not need an overlay.
On a tablet, the table should stay usable for row selection.

### Suspected cause

The responsive layout reused a modal sheet for details.
It blocks the table on tablet widths.

### Acceptance

- Details are not a modal overlay.
- The table stays clickable while details are open.
- A row click updates details.
- On a tablet, details use a side or bottom panel that leaves the
  table visible.
- The details panel can be collapsed or closed.
- No backdrop and no inert table for details.
- Focus is not trapped in details.
- `Esc` and the close button close details.
- The phone layout is confirmed separately.

### User answer

The phone uses a full-screen details view.
The tablet uses a non-modal bottom panel.
The table stays clickable on the tablet.
