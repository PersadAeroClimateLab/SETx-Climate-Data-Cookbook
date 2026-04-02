require(['base/js/events'], function(events) {
    events.on('notebook_loaded.Notebook', function() {
        // Disable output scrolling threshold
        IPython.OutputArea.auto_scroll_threshold = -1;

        // Hide code cells
        Jupyter.notebook.get_cells().forEach(function(cell) {
            if (cell.cell_type === 'code') {
                cell.input.hide();
            }
        });
    });

    // Also catch outputs generated after notebook load
    events.on('output_added.OutputArea', function() {
        IPython.OutputArea.auto_scroll_threshold = -1;
    });
});