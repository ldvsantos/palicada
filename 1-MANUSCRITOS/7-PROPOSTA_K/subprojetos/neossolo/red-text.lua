-- red-text.lua — Lua filter for Quarto/Pandoc
-- Converts [text]{.red} spans to \textcolor{red}{text} in LaTeX
-- and to <span style="color:red">text</span> in HTML.
-- Inner content (math, citations, cross-references) is processed normally by Pandoc.

function Span(el)
  if el.classes:includes("red") then
    if FORMAT:match("latex") then
      local result = pandoc.List()
      result:insert(pandoc.RawInline("latex", "\\textcolor{red}{"))
      result:extend(el.content)
      result:insert(pandoc.RawInline("latex", "}"))
      return result
    else
      el.attributes["style"] = "color: red;"
      return el
    end
  end
end
