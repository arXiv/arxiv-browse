function colors_interpolateRdBu(value) {
  color_arr = ["rgb(103, 0, 31)", "rgb(110, 2, 32)", "rgb(118, 5, 33)", "rgb(125, 7, 35)", "rgb(133, 10, 36)", "rgb(140, 13, 37)", "rgb(147, 16, 39)", "rgb(153, 20, 41)", "rgb(160, 23, 42)", "rgb(166, 27, 44)", "rgb(172, 32, 47)", "rgb(177, 37, 49)", "rgb(182, 42, 52)", "rgb(187, 48, 55)", "rgb(191, 54, 58)", "rgb(195, 61, 61)", "rgb(199, 68, 64)", "rgb(203, 74, 68)", "rgb(206, 81, 72)", "rgb(210, 88, 76)", "rgb(213, 96, 80)", "rgb(216, 103, 85)", "rgb(219, 110, 89)", "rgb(223, 116, 94)", "rgb(226, 123, 99)", "rgb(228, 130, 104)", "rgb(231, 137, 110)", "rgb(234, 143, 115)", "rgb(236, 150, 121)", "rgb(238, 156, 127)", "rgb(241, 163, 133)", "rgb(242, 169, 139)", "rgb(244, 174, 145)", "rgb(245, 180, 152)", "rgb(247, 186, 158)", "rgb(248, 191, 164)", "rgb(249, 196, 171)", "rgb(249, 201, 177)", "rgb(250, 206, 183)", "rgb(250, 210, 190)", "rgb(251, 215, 196)", "rgb(251, 219, 201)", "rgb(250, 222, 207)", "rgb(250, 226, 212)", "rgb(250, 229, 217)", "rgb(249, 232, 221)", "rgb(248, 234, 226)", "rgb(247, 236, 229)", "rgb(245, 237, 233)", "rgb(244, 239, 236)", "rgb(242, 239, 238)", "rgb(239, 240, 240)", "rgb(237, 239, 241)", "rgb(234, 239, 242)", "rgb(230, 238, 242)", "rgb(227, 237, 242)", "rgb(223, 235, 242)", "rgb(219, 233, 241)", "rgb(214, 231, 240)", "rgb(210, 229, 239)", "rgb(205, 227, 238)", "rgb(200, 224, 237)", "rgb(194, 221, 235)", "rgb(189, 219, 234)", "rgb(183, 216, 232)", "rgb(177, 212, 231)", "rgb(170, 209, 229)", "rgb(164, 206, 227)", "rgb(157, 202, 225)", "rgb(150, 198, 223)", "rgb(143, 194, 221)", "rgb(136, 190, 218)", "rgb(129, 185, 216)", "rgb(122, 181, 213)", "rgb(114, 176, 211)", "rgb(107, 172, 208)", "rgb(100, 167, 206)", "rgb(93, 162, 203)", "rgb(87, 157, 201)", "rgb(80, 153, 198)", "rgb(75, 148, 196)", "rgb(69, 143, 193)", "rgb(64, 138, 191)", "rgb(59, 134, 188)", "rgb(55, 129, 185)", "rgb(51, 124, 183)", "rgb(47, 120, 179)", "rgb(44, 115, 176)", "rgb(40, 110, 172)", "rgb(37, 105, 168)", "rgb(34, 101, 163)", "rgb(31, 96, 158)", "rgb(28, 90, 153)", "rgb(25, 85, 147)", "rgb(22, 80, 140)", "rgb(19, 75, 133)", "rgb(16, 70, 126)", "rgb(13, 64, 119)", "rgb(11, 59, 112)", "rgb(8, 53, 104)", "rgb(5, 48, 97)"]
  return color_arr[parseInt(value*100)];
}

var InfluenceFlower = class InfluenceFlower {

  constructor(w, h) {
    this.width = w;
    this.height = h;
    this.start_petals = 25;
    this.start_order = "ratio";
  }

  drawInfoBox(flower_type, svg_id) {
    var parentDiv = document.getElementById(svg_id).parentElement;
    if (parentDiv.getElementsByClassName("flower-infobox").length > 0) return;
    var infoDiv = document.createElement("div");
    infoDiv.setAttribute("class", "flower-infobox");
    infoDiv.innerHTML = "<div class='flower-text'><span class='text-blue'>Blue arcs</span> denote "
      + "<i>incoming</i> influence from the " + flower_type + "s to the paper, "
      + "with their thickness proportional to the number of <i>references</i> made.</div>"
      + "<div class='flower-text'><span class='text-red'>Red arcs</span> denote "
      + "<i>outgoing</i> influence from the paper to the " + flower_type + "s, "
      + "with their thickness proportional to the number of <i>citations</i> recieved.</div>"
    parentDiv.appendChild(infoDiv);
  }

  drawFlower(svg_id, flower_type, data, idx, ego_url_base) {
    this.svg = [];
    this.node_out = {};
    this.text_out = [];

    const colors = colors_interpolateRdBu;
    const selcolor = [colors(0.2), colors(0.8)];
    const norcolor = [colors(0.25), colors(0.75)];

    this.window_scaling_factor = Math.min(1200, this.width)/1000;
    this.node_max_area = 1000.0;
    this.magf = Math.min(200, 200*this.window_scaling_factor);
    this.center = [this.width*0.5, (this.height+this.magf)*0.52];

    var total_entity_num = data["total"];
    var nodes = data["nodes"];
    var links = data["links"];
    var bars = data["bars"];

    this.svg[idx] = document.getElementById(svg_id);
    this.svg[idx].setAttribute("width", this.width);
    this.svg[idx].setAttribute("height", this.height);
    this.drawInfoBox(flower_type, svg_id);

    // Ordering
    var ordering = this.reorder(this.start_petals, this.start_order, data);
    var [xpos, ypos] = this.gen_pos(this.start_petals);

    // flower graph edge arrow
    var defs = document.createElement("defs");
    for (var i = 0; i < links.length; i++) {
      var d = links[i];
      var marker = document.createElement('marker');
      marker.setAttribute("id", d.gtype+"_"+d.type+"_"+d.id);
      marker.setAttribute("viewBox", "0 -5 10 10");
      marker.setAttribute("refX", Math.max(9, this.nodeRadius(d.padding)/this.window_scaling_factor));
      marker.setAttribute("refY", -d.padding);
      marker.setAttribute("markerWidth", this.window_scaling_factor*this.arrow_size_calc(d.weight));
      marker.setAttribute("markerHeight", this.window_scaling_factor*this.arrow_size_calc(d.weight));
      marker.setAttribute("markerUnits", "userSpaceOnUse");
      marker.setAttribute("orient", "auto")
      var m_path = document.createElement('path');
      m_path.setAttribute("d", "M0,-5L10,0L0,5");
      if (d.type == "in") m_path.style.fill = norcolor[0];
      else m_path.style.fill = norcolor[1];
      marker.appendChild(m_path);
      defs.appendChild(marker);
    }

    this.svg[idx].innerHTML = defs.outerHTML;

    var node_g = document.createElement("g");
    var link_g = document.createElement("g");
    var text_g = document.createElement("g");

    // flower graph nodes
    for (var i = 0; i < nodes.length; i++) {
      var d = nodes[i];
      var node = document.createElement('circle');
      node.setAttribute("id", d.id);
      node.setAttribute("name", d.name);
      node.setAttribute("class", "hl-circle");
      if (ordering[d.id] == undefined) {
        node.setAttribute("xpos", this.center[0]);
        node.setAttribute("ypos", this.center[1]);
        node.setAttribute("cx", this.center[0]);
        node.setAttribute("cy", this.center[1]);
      } else {
        node.setAttribute("xpos", this.center[0]+this.magf*xpos[ordering[d.id]]);
        node.setAttribute("ypos", this.center[1]-this.magf*ypos[ordering[d.id]]);
        node.setAttribute("cx", this.center[0]+this.magf*xpos[ordering[d.id]]);
        node.setAttribute("cy", this.center[1]-this.magf*ypos[ordering[d.id]]);
      }
      node.setAttribute("gtype", d.gtype);
      node.setAttribute("r", this.nodeRadius(d.size));
      if (d.id == 0) node.style.fill = "#fff";
      else node.style.fill = colors(d.weight);
      if (d.bloom_order > this.start_petals) {
        node.style.visibility = "hidden";
        node.style.opacity = 0.0;
      } else {
        node.style.visibility = "visible";
        node.style.opacity = 1.0;
      }
      // node.setAttribute('onmouseover', `highlight_on(${d.id})`);
      // node.setAttribute('onmouseout', 'highlight_off()');

      this.node_out[i] = node;
      node_g.appendChild(node);
    }

    // flower graph node text
    for (var i = 0; i < nodes.length; i++) {
      var d = nodes[i];
      var text = document.createElement('text');
      text.setAttribute("id", d.id);
      text.setAttribute("gtype", d.gtype);
      if (d.id == 0) {
        text.setAttribute("class", "hl-text node-ego-text");
      } else {
        text.setAttribute("class", "hl-text node-text");
      }

      if (ordering[d.id] == undefined) {
        text.setAttribute("x", this.center[0]);
        text.setAttribute("y", this.center[1]);
      } else {
        text.setAttribute("x", this.text_order_xpos(d, xpos, ordering));
        text.setAttribute("y", this.text_order_ypos(d, xpos, ypos, this.start_petals, ordering));
      }
      text.setAttribute("text-anchor", this.text_order_anchor(d, xpos, ordering));
      text.setAttribute("node_size", d.size);

      var capName = this.capitalizeString(d.id==0, d.gtype, d.name);
      var egoLink = ego_url_base+"&tab="+idx;
      var influencemap_url_base = "http://influencemap.ml/submit/?id="
      if (d.id == 0) {
        text.innerHTML = "<a href='"+egoLink+"' target='_blank'>"+capName+"</a>";
      } else {
        // text.innerHTML = "<a href='"+influencemap_url_base+d.url+"' target='_blank'>"+capName+"</a>";
        text.innerHTML = capName;
      }

      if (d.coauthor == 'False') text.style.fill = "black";
      else text.style.fill = "gray";
      if (d.bloom_order > this.start_petals) text.style.visibility = "hidden";
      else text.style.visibility = "visible";
      text.style.opacity = 1.0;

      text_g.appendChild(text);
    }

    // flower graph edges
    for (var i = 0; i < links.length; i++) {
      var d = links[i];
      var link = document.createElement('path');
      link.setAttribute("id", d.id);
      link.setAttribute("d", this.linkArc(idx, d, true));
      link.setAttribute("gtype", d.gtype);
      link.setAttribute("class", "hl-link " + d.type);
      link.setAttribute("marker-end", "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")");
      link.setAttribute("type", d.type);

      if(d.type == "in") link.style.stroke = norcolor[0];
      else link.style.stroke = norcolor[1];
      if (d.bloom_order > this.start_petals) {
        link.style.visibility = "hidden";
        link.style.opacity = 0.0;
      } else {
        link.style.visibility = "visible";
        link.style.opacity = 1.0;
      }
      link.style.strokeWidth = this.window_scaling_factor*this.arrow_width_calc(d.weight);

      link_g.appendChild(link);
    }

    this.svg[idx].innerHTML += link_g.outerHTML + node_g.outerHTML + text_g.outerHTML;

  }

  linkArc(idx, d, bloom) {
    var source = this.node_out[d.source],
        target = this.node_out[d.target];
    var sx, sy, tx, ty;
    if (bloom) {
      sx = parseInt(source.getAttribute("xpos")), sy = parseInt(source.getAttribute("ypos")),
      tx = parseInt(target.getAttribute("xpos")), ty = parseInt(target.getAttribute("ypos"));
    } else {
      sx = parseInt(source.getAttribute("cx")), sy = parseInt(source.getAttribute("cy")),
      tx = parseInt(target.getAttribute("cx")), ty = parseInt(target.getAttribute("cy"));
    }
    var dx = tx-sx,
        dy = ty-sy,
        dr = Math.sqrt(dx * dx + dy * dy)*2;
    return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,1 " + tx + "," + ty;
  }

  nodeRadius(size) {
    return (Math.sqrt((this.node_max_area/Math.PI)*size)*this.window_scaling_factor);
  }

  arrow_width_calc(weight) {
    if (weight == 0) { return 0; }
    else { return 1+8*weight; }
  }

  arrow_size_calc(weight) {
    if (weight == 0) { return 0; }
    else { return 15; }
  }

  capitalizeString(isEgo, entity_type, string) {
    var words = string.split(' ');
    var res = [];
    if ((entity_type == "conf" && words.length == 1 && string.length < 8) // for conf names
      || (entity_type == "inst" && words.length == 1 && string.length < 5)) // for inst names
      return string.toUpperCase();

    var stopwords = ["and", "or", "of", "the", "at", "on", "in", "for"],
        capwords = ["ieee", "acm", "siam", "eth", "iacr", "ieice"];
    var spacialcase = {"arxiv": "arXiv:"}
    for (var i = 0; i < words.length; i++) {
        var fwords = words[i];
        if (capwords.includes(fwords)) {
          fwords = words[i].toUpperCase();
        } else if (spacialcase[fwords] != undefined) {
          fwords = spacialcase[words[i]];
        } else if (!stopwords.includes(fwords)) {
          fwords = words[i].charAt(0).toUpperCase() + words[i].slice(1);
        }
        res.push(fwords);
    }

    if (!isEgo && string.length > 30) {
      var shorten = res.slice(0,5).join(' ');
      if (res.length > 6 ) shorten = shorten + "...";
      return shorten;
    } else return res.join(' ');
  }

  // ---------- Ordering and Sorting ----------
  reorder(num, order, data) {
    var sortable_data = data.nodes
      .slice(1)
      .filter(function(d) { return d.bloom_order <= num; } );

    var sort_func = this.ratio_order;
    var sort_index = {0:0};

    for (var i in sortable_data.sort(sort_func)) {
      sort_index[sortable_data[i].id] = parseInt(i) + 1;
    }
    return sort_index;
  }

  ratio_order(a, b) {
    const SORT_TOL = 1e-9;
    var a_val = a.ratio + SORT_TOL * a.dif;
    var b_val = b.ratio + SORT_TOL * b.dif;
    return - (a_val - b_val);
  }

  // ---------- Transform and Positions ----------
  linspace(start, end, num) {
    if (num > 1) {
      var step = (end - start) / (num - 1);
    }
    else {
      var step = 0;
    }
    var lin = [];

    for (var i = 0; i < num; i++) {
      lin.push(start + i * step);
    }
    return lin;
  }

  gen_pos(num) {
    const RADIUS = 1.2;
    if (num > 25) {
      var angles = this.linspace(Math.PI * (1 + (num - 25) / num / 2), - Math.PI * (num - 25) / num / 2, num);
    }
    else if (num < 10) {
      var angles = this.linspace(Math.PI * (0.5 + num / 20), Math.PI * (0.5 - num / 20), num);
    }
    else {
      var angles = this.linspace(Math.PI, 0, num);
    }

    var x_pos = {0: 0};
    var y_pos = {0: 0};
    for (var i in angles) {
      var angle = angles[i];
      x_pos[parseInt(i)+1] = RADIUS * Math.cos(angle);
      y_pos[parseInt(i)+1] = RADIUS * Math.sin(angle);
    }
    return [x_pos, y_pos];
  }

  text_order_xpos(d, xpos, ordering) {
    var shift = 0;
    var circ_dif = 5;
    var xval = xpos[ordering[d.id]];
    if (xval < -.3) shift -= this.nodeRadius(d.size) + circ_dif;
    if (xval > .3) shift += this.nodeRadius(d.size) + circ_dif;
    return this.center[0] + this.magf*xval + shift;
  }

  text_order_ypos(d, xpos, ypos, num, ordering) {
    var shift = 0;
    var scale = num/20;
    var xval = xpos[ordering[d.id]];
    var yval = ypos[ordering[d.id]];

    for(var i = 6; i >= 0; i--) {
        var xpos_p = i/10+0.05;
        if (d.id > 0 && -xpos_p < xval && xval < xpos_p) shift -= (7-i)*scale;
    }
    // Title
    if (d.id == 0) {
        shift += 50;
    }
    return this.center[1] - this.magf*yval + shift;
  }

  text_order_anchor(d, xpos, ordering) {
    var xval = xpos[ordering[d.id]];
    if (xval < -0.1) return "end";
    else if (xval > 0.1) return "start";
    else return "middle";
  }
};


function highlight_on(id) {
  console.log("highlight ON", id);
}

function highlight_off(id) {
  console.log("highlight OFF", id);
}


function openTab(evt, tab_id) {
  var tabcontent = document.getElementsByClassName("tab-flower");
  var tabbuttons = document.getElementsByClassName("tab-btn");
  for (var i = 0; i < tabcontent.length; i++) {
    tabcontent[i].classList.remove("active");
    tabbuttons[i].parentNode.classList.remove("active");
  }
  document.getElementById(tab_id).classList.add("active");
  evt.currentTarget.parentNode.classList.add("active");
}

function drawInfluenceFlowers(data) {
  var container_w = document.getElementById("influenceflower-output-graph").offsetWidth;
  var padding_w = 10;
  var flowers = new InfluenceFlower(container_w-padding_w, 400);
  var ego_url_base = data.url_base;
  var author_data = data.author[0];
  var conf_data = data.conf[0];
  var inst_data = data.inst[0];
  var fos_data = data.fos[0];
  flowers.drawFlower("flower-graph-author", "author", author_data, 0, ego_url_base);
  flowers.drawFlower("flower-graph-venue", "venue", conf_data, 1, ego_url_base);
  flowers.drawFlower("flower-graph-inst", "institution", inst_data, 2, ego_url_base);
  flowers.drawFlower("flower-graph-topic", "research field", fos_data, 3, ego_url_base);
}
