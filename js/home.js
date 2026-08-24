var homeArtworkFitSchedule = null;
var HOME_DESKTOP_MQ = window.matchMedia('(min-width: 761px)');

function measureHomeFoldCaptionMin() {
  if (!HOME_DESKTOP_MQ.matches) {
    document.documentElement.style.removeProperty('--home-caption-fold-min-h');
    return 0;
  }
  var cap = document.querySelector('.home-caption--fold');
  if (!cap) return 0;
  var h = Math.ceil(cap.getBoundingClientRect().height);
  var pad =
    parseFloat(getComputedStyle(cap).paddingTop) +
    parseFloat(getComputedStyle(cap).paddingBottom);
  var minH = h + pad + 2;
  document.documentElement.style.setProperty('--home-caption-fold-min-h', minH + 'px');
  return minH;
}

function scheduleHomeArtworkFit() {
  if (homeArtworkFitSchedule) homeArtworkFitSchedule();
}

function initHomeContent() {
  var visual = document.getElementById('home-visual');
  var fold = document.querySelector('.home-fold');
  var caption = document.querySelector('.home-caption--fold');
  var foldRoot = document.getElementById('home-caption-fold');
  var restRoot = document.getElementById('home-caption-rest');
  var captionData = window.SITE && SITE.homeCaption;

  if (captionData && (foldRoot || restRoot)) {
    function lineHtml(text, cls) {
      return '<span class="home-caption__line ' + cls + '">' + text + '</span>';
    }

    function renderGroup(lines) {
      if (!lines.length) return '';
      return (
        '<div class="home-caption__group">' +
        lines.join('') +
        '</div>'
      );
    }

    var titleLines = [];
    if (captionData.year) {
      titleLines.push(lineHtml(captionData.year, 'home-caption__year'));
    }
    if (captionData.title) {
      titleLines.push(lineHtml(captionData.title, 'home-caption__title'));
    }

    var metaLines = [];
    if (captionData.medium) {
      metaLines.push(lineHtml(captionData.medium, 'home-caption__meta'));
    }
    if (captionData.size) {
      metaLines.push(lineHtml(captionData.size, 'home-caption__meta'));
    }

    var poemLines = (captionData.poem || [])
      .filter(Boolean)
      .map(function (line) {
        return lineHtml(line, 'home-caption__poem');
      });

    var mobileMq = window.matchMedia('(max-width: 760px)');

    function renderCaptionLayout() {
      if (!foldRoot) return;
      if (mobileMq.matches) {
        foldRoot.innerHTML =
          renderGroup(titleLines) + renderGroup(metaLines) + renderGroup(poemLines);
        if (restRoot) restRoot.innerHTML = '';
      } else {
        foldRoot.innerHTML = renderGroup(titleLines);
        if (restRoot) {
          restRoot.innerHTML = renderGroup(metaLines) + renderGroup(poemLines);
        }
      }
    }

    function onCaptionLayoutChange() {
      renderCaptionLayout();
      measureHomeFoldCaptionMin();
      scheduleHomeArtworkFit();
    }

    onCaptionLayoutChange();
    if (typeof mobileMq.addEventListener === 'function') {
      mobileMq.addEventListener('change', onCaptionLayoutChange);
    } else if (typeof mobileMq.addListener === 'function') {
      mobileMq.addListener(onCaptionLayoutChange);
    }
  }

  if (visual && window.SITE) {
    visual.src = SITE.homeVisual;
    visual.alt = '';
  }

  if (visual && fold && window.ArtworkSize) {
    measureHomeFoldCaptionMin();
    homeArtworkFitSchedule = ArtworkSize.bindStandardPageArtworkFit({
      container: fold,
      img: visual,
      captionEl: caption,
      fitOptions: {
        useViewportHeight: true,
        useUniformPageWidth: true,
        get captionMinReserve() {
          return measureHomeFoldCaptionMin();
        },
      },
      onMetrics: function (metrics) {
        var stage = document.querySelector('.home-stage');
        if (stage && metrics.width > 0) {
          stage.style.setProperty('--home-artwork-w', Math.round(metrics.width) + 'px');
        }
      },
    });
  }
}

initHomeContent();
