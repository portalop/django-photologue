  jQuery(function($){

    var jcrop_api,
        boundx,
        boundy,

        // Grab some information about the preview pane
        $preview = $('#preview-pane'),
        $pcnt = $('#preview-pane .preview-container'),
        $pimg = $('#preview-pane .preview-container img'),

        xsize = $pimg.width(),
        ysize = $pimg.height(),
        fixed_ratio = $('#target').data("fixed-ratio"),

        attr_width = $pimg.attr('width'),
        attr_height = $pimg.attr('height');

        attr_width = attr_width?parseInt(attr_width, 10):0;
        attr_height = attr_height?parseInt(attr_height, 10):0;

    $('#target').Jcrop({
      bgOpacity: 0.5,
      bgColor:   'white',
      addClass:  'jcrop-light',
      minSize:   [attr_width, attr_height],
      onChange:  showCoords,
      onSelect:  showCoords,
      onRelease: clearCoords
    },function(){
      jcrop_api = this;
      // Use the API to get the real image size
      var bounds = jcrop_api.getBounds();
      boundx = bounds[0];
      boundy = bounds[1];
      if (fixed_ratio)
        jcrop_api.setOptions({ aspectRatio: xsize / ysize });
      jcrop_api.ui.selection.addClass('jcrop-selection');

      $pcnt.css({
        width: xsize + 'px',
        height: ysize + 'px'
      })
      jcrop_api.setSelect([$('#id_x').val(),$('#id_y').val(),parseInt($('#id_x').val()) + parseInt($('#id_width').val()),parseInt($('#id_y').val()) + parseInt($('#id_height').val())]);
      jcrop_api.setOptions({ bgFade: true });
      // Move the preview into the jcrop container for css positioning
      $preview.appendTo(jcrop_api.ui.holder);
    });

    $('#coords').on('change','input',function(e){
      var x = $('#id_x').val(),
          y = $('#id_y').val(),
          width = $('#id_width').val(),
          height = $('#id_height').val();
      jcrop_api.setSelect([x,y,x + width,y + height]);
    });

    // Simple event handler, called from onChange and onSelect
    // event handlers, as per the Jcrop invocation above
    function showCoords(c)
    {
      $('#id_x').val(c.x);
      $('#id_y').val(c.y);
      $('#id_width').val(Math.round(c.w));
      $('#id_height').val(Math.round(c.h));
      $preview.css({right: '-' + (Math.round(attr_width?attr_width:attr_height*c.w/c.h) + 40) + 'px'});
      if (parseInt(c.w) > 0)
      {
        var rx, ry;
        if (!fixed_ratio)
        {
          $pcnt.css({
            width: Math.round(attr_width?attr_width:attr_height*c.w/c.h) + 'px',
            height: Math.round(attr_height?attr_height:attr_width*c.h/c.w) + 'px'
          });
          rx = $pcnt.width() / c.w;
          ry = $pcnt.height() / c.h;
        }
        else
        {
          rx = xsize / c.w;
          ry = ysize / c.h;
        }
        $pimg.css({
          width: Math.round(rx * boundx) + 'px',
          height: Math.round(ry * boundy) + 'px',
          marginLeft: '-' + Math.round(rx * c.x) + 'px',
          marginTop: '-' + Math.round(ry * c.y) + 'px'
        });
      }
    };

    function clearCoords()
    {
      $('#coords input').val('0');
    };
  });