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
        <td>Creation:
            <div  id="creation-date" class="input-group date" data-provide="datepicker">
                <input type="text" class="form-control">
                <div class="input-group-addon">
                    <span class="glyphicon glyphicon-th"></span>
                </div>
            </div>
        </td>
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
    load(opts, this);
    $('.selectpicker').selectpicker('render');
</hails>

