<hails>
<ul class="pagination">
    <li id="prev_page">
      <a href="#" aria-label="Previous">
        <span aria-hidden="true">&laquo;</span>
      </a>
    </li>
    <li each={page, p in iter_pages}>
    <a href="#" if={page} class='page' id="page_{page}"><span>{page}</span></a>
    <span if={!page}>…</span>
    </li>
    <li id="next_page">
      <a href="#" aria-label="Next">
        <span aria-hidden="true">&raquo;</span>
      </a>
    </li>
</ul>
<table class="hails pure-table">
    <thead>
    <tr>
        <td>Id</td>
        <td>Creation</td>
        <td><select class="selectpicker" multiple title="Added by"
                name="moteur" data-live-search="true" id="moteurselect">
                <option each={mo, m in moteurs}>{mo}</option>
        </select></td>
        <td><select class="selectpicker" multiple title="Operator"
                name="operateur" data-live-search="true" id="operateurselect">
                <option each={op, o in operators}>{op}</option>
        </select></td>
        <td><select class="selectpicker" multiple title="Current status"
                name="status" data-live-search="true" id="statusselect">
            <option each={st, s in statuses}>{st}</option>
        </select></td>
    </tr>
    </thead>
    <tbody>
        <tr each={hails}>
            <td><a href="/hails/{id}/_explore">{id}</a></td>
            <td>{creation_datetime}</td>
            <td>{added_by}</td>
            <td>{operateur}</td>
            <td>{status}</td>
        </tr>
    </tbody>
    </table>
    this.hails = [];
    var selection = {"moteur": [], "operateur": [], "status": []};
    var page = 1;
    load(apikey) {
        var headers = {"Accept": "application/json",
                       "X-VERSION": 2,
                       "X-API-KEY": opts.apikey
        };
        var s = this;
        var getHails = function(page) {
            selection = {"moteur": [], "operateur": [], "status": []};
            var selected = $(".selectpicker option:selected").toArray();
            var params = selected.map(
                    function(o){
                        selection[o.parentElement.name].push(o.value);
                        return o.parentElement.name+'='+o.value
                    })
                .join('&');
            fetch('/hails/?p='+page+'&'+params, {headers:headers})
                .then(function(response) {
                    return response.json();
                })
                .then(function(r) {
                    this.hails = r.data;
                    this.moteurs = opts.moteurs;
                    this.operators = opts.moteurs;
                    this.statuses = opts.statuses;
                    this.iter_pages = r.meta.iter_pages;
                    this.update();
                    $('.selectpicker').selectpicker();
                    for (var id_ in selection) {
                        $('#'+id_+'select').selectpicker('val', selection[id_]);
                    }
                    $('.selectpicker').selectpicker('refresh');
                    $('.selectpicker').on('change', function(){
                        getHails(1);
                    });
                    if(r.meta.prev_page != null) {
                        $('#prev_page').removeClass('disabled');
                        document.getElementById('prev_page').onclick = function() {
                            getHails(r.meta.prev_page);
                        };
                    } else {
                        $('#prev_page').addClass('disabled');
                    }
                    if(r.meta.next_page) {
                        $('#next_page').removeClass('disabled');
                        document.getElementById('next_page').onclick = function() {
                            getHails(r.meta.next_page);
                        };
                    } else {
                        $('#next_page').addClass('disabled');
                    }
                    [].slice.call(document.getElementsByClassName('page')).map(
                            function(a){
                                if (a.tagName != 'A') {
                                    return;
                                }
                                var page_parsed = parseInt(a.children[0].textContent);
                                if (page_parsed == NaN) {
                                    return;
                                }
                                a.onclick = function() {getHails(page_parsed);};
                                var page_a = $('#'+a.id);
                                var page_li = page_a.parent();
                                //debugger;
                                page_li.removeClass('active');
                                if (page_parsed == page) {
                                    console.log('active');
                                    page_li.addClass('active');
                                }
                            }
                    );
                }.bind(s), console.error.bind(console));
        };
        getHails(1);
    }
    this.load();
    $('.selectpicker').selectpicker('render');
</hails>

