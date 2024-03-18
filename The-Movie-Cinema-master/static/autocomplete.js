new autoComplete({
    data: {                              // 数据源 [数组, 函数, 异步] | (必需)
      src: films,
    },
    selector: "#autoComplete",           // 输入字段选择器 | (可选)
    threshold: 2,                        // 触发引擎的最小字符长度 | (可选)
    debounce: 100,                       // 引擎启动后的持续时间 | (可选)
    searchEngine: "strict",              // 搜索引擎类型/模式 | (可选)
    resultsList: {                       // 渲染结果列表对象 | (可选)
        render: true,
        container: source => {
            source.setAttribute("id", "movie_list");
        },
        destination: document.querySelector("#autoComplete"), // 结果列表的位置 | (可选)
        position: "afterend",
        element: "ul"
    },
    maxResults: 5,                         // 渲染结果的最大数量 | (可选)
    highlight: true,                       // 高亮匹配结果 | (可选)
    resultItem: {                          // 渲染结果项 | (可选)
        content: (data, source) => {
            source.innerHTML = data.match;
        },
        element: "li"
    },
    noResults: () => {                     // 没有结果时的动作脚本 | (可选)
        const result = document.createElement("li");
        result.setAttribute("class", "no_result");
        result.setAttribute("tabindex", "1");
        result.innerHTML = "No Results";
        document.querySelector("#autoComplete_list").appendChild(result);
    },
    onSelection: feedback => {             // 选择事件的动作脚本 | (可选)
        document.getElementById('autoComplete').value = feedback.selection.value;
    }
});