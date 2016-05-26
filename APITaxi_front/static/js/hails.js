<hails>
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
    load(apikey) {
        var headers = {"Accept": "application/json",
                       "X-VERSION": 2,
                       "X-API-KEY": opts.apikey
        };
        var s = this;
        var getHails = function(url) {
            fetch(url, {headers:headers})
                .then(function(response) {
                    return response.json();
                })
                .then(function(r) {
                    this.hails = r.data;
                    this.moteurs = opts.moteurs;
                    this.operators = opts.moteurs;
                    this.statuses = opts.statuses;
                    this.update();
                    $('.selectpicker').selectpicker();
                    for (var id_ in selection) {
                        $('#'+id_+'select').selectpicker('val', selection[id_]);
                    }
                    $('.selectpicker').selectpicker('refresh');
                    $('.selectpicker').on('change', function(){
                        selection = {"moteur": [], "operateur": [], "status": []};
                        var selected = $(".selectpicker option:selected").toArray();
                        var params = selected.map(
                                function(o){
                                    selection[o.parentElement.name].push(o.value);
                                    return o.parentElement.name+'='+o.value
                                })
                            .join('&');
                        console.log(params);
                        getHails('/hails/?'+params);
                    });
                }.bind(s), console.error.bind(console));
        };
        getHails('/hails/');
    }
    this.load();
    $('.selectpicker').selectpicker('render');
</hails>

