function load(opts, other) {
    other.hails = [];
    var selection = {"moteur": [], "operateur": [], "status": []};
    var page = 1;
    var headers = {"Accept": "application/json",
                   "X-VERSION": 2,
                   "X-API-KEY": opts.apikey
    };
    var getHails = function(page) {
        selection = {"moteur": [], "operateur": [], "status": []};
        var selected = $(".selectpicker option:selected").toArray();
        var params = selected.map(
                function(o){
                    selection[o.parentElement.name].push(o.value);
                    return o.parentElement.name+'='+o.value
                });
        params.push('date='+$('#datetimepicker1 input').val());
        fetch('/hails/?p='+page+'&'+params.join('&'), {headers:headers})
            .then(function(response) {
                return response.json();
            })
            .then(function(r) {
                other.hails = r.data;
                other.moteurs = opts.moteurs;
                other.operators = opts.operateurs;
                other.statuses = opts.statuses;
                other.iter_pages = r.meta.iter_pages;
                other.update();
                $('.selectpicker').selectpicker();
                for (var id_ in selection) {
                    $('#'+id_+'select').selectpicker('val', selection[id_]);
                }
                $('.selectpicker').selectpicker('refresh');
                $('.selectpicker').on('change', function(){
                    getHails(1);
                });
                $('#datetimepicker1').datetimepicker({
                    format: "YYYY/MM/DD hh:mm:00"
                }).on('dp.change', function (e) {
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
                                page_li.addClass('active');
                            }
                        }
                );
            }.bind(s), console.error.bind(console));
    };
    getHails(1);
}
