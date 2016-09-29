import 'codemirror/lib/codemirror.css';

import 'codemirror/addon/selection/active-line';
import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/addon/edit/closebrackets';
import 'codemirror/addon/display/placeholder';
import 'codemirror/mode/clojure/clojure';
import 'codemirror/mode/javascript/javascript';

import React from 'react';
import ReactDOM from 'react-dom';
import _CodeMirror from 'codemirror';

import './console.css';


class CodeMirror extends React.Component {
  getContent() {
    return this.codeMirror ? this.codeMirror.getValue() : this.props.content || '';
  }
  componentDidMount() {
    const textAreaNode = ReactDOM.findDOMNode(this.refs.container);
    this.codeMirror = _CodeMirror(textAreaNode, this.props.options);
    this.codeMirror.setOption('extraKeys', this.props.keyMap);
    this.codeMirror.setValue(this.props.content || '');
  }
  render() {
    if (this.props.readOnly && this.codeMirror) {
      this.codeMirror.setValue(this.props.content || '');
    }
    return <div ref="container"/>
  }
}
CodeMirror.propTypes = {
  readOnly: React.PropTypes.bool,
  content: React.PropTypes.string,
  options: React.PropTypes.object,
  keyMap: React.PropTypes.object
};


class QueryComponent extends React.Component {
  getQuery() {
    return this.refs.editor.getContent();
  }
  render() {
    let osx = navigator.platform == "MacIntel";
    let run_key_name = osx ? String.fromCharCode(8984) + "Enter" : "Ctrl+Enter";
    let options = {
      placeholder: "Type your query here and press " + run_key_name,
      viewportMargin: Infinity,
      matchBrackets: true,
      autoCloseBrackets: "[](){}\"\"",
      mode: "clojure"
    };
    let keyMap = {
      Tab: function (cm) {
        let spaces = new Array(_CodeMirror.getOption('indentUnit') + 1).join(' ');
        _CodeMirror.replaceSelection(spaces);
      }
    };
    keyMap[osx ? "Cmd-Enter" : "Ctrl-Enter"] = this.props.onSubmit;

    return (
      <div className="query">
        <CodeMirror ref="editor" options={options} keyMap={keyMap}/>
      </div>
    )
  }
}
QueryComponent.propTypes = {
  onSubmit: React.PropTypes.func
};


class ResultComponent extends React.Component {
  render() {
    let options = {
      mode: {name: "javascript", json: true},
      readOnly: true
    };
    return (
      <div className="result">
        <CodeMirror options={options} content={this.props.content} readOnly={true}/>
      </div>
    )
  }
}
ResultComponent.propTypes = {
  content: React.PropTypes.string
};


class DocsComponent extends React.Component {
  render() {
    let options = {readOnly: true};
    return (
      <div className="docs">
        <CodeMirror options={options} content={this.props.content} readOnly={true}/>
      </div>
    )
  }
}
DocsComponent.propTypes = {
  content: React.PropTypes.string
};


function parseJSON(response) {
  if (response.headers.get('content-type') == 'application/json') {
    return response.json().then((data) => {
      return {status: response.status, data: data};
    });
  } else {
    throw new Error('Parse error');
  }
}

function checkStatus(response) {
  if (response.status == 200) {
    return response;
  } else {
    throw new Error(response.statusText);
  }
}


class Console extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      displaySidebar: false,
      documentation: null,
      documentationLoading: false,
      result: null,
      resultLoading: false
    };
  }
  submitQuery() {
    this.setState({
      resultLoading: true
    });
    fetch(window.URLS.index, {
      method: 'POST',
      headers: {'Content-Type': 'application/edn'},
      body: this.refs.query.getQuery()
    })
      .then(parseJSON)
      .then(({status, data}) => {
        let result;
        if (status == 200) {
          result = JSON.stringify(data, null, "  ");
        } else if (status == 400) {
          var report = 'Errors:\n';
          for (var i=0; i < data.errors.length; i++) {
              report = report + '- ' + data.errors[i] + '\n'
          }
          result = report;
        } else if (status == 500) {
          result = data.traceback || 'Server error';
        }
        this.setState({result: result,
                       resultLoading: false});
      })
      .catch((error) => {
        this.setState({
          result: error.message,
          resultLoading: false
        });
      });
  }
  toggleSidebar() {
    if (this.state.documentation == null && !this.state.displaySidebar) {
      this.setState({
        displaySidebar: true,
        documentationLoading: true
      });
      fetch(window.URLS.docs)
        .then(checkStatus)
        .then((response) => { return response.text() })
        .then((body) => {
          this.setState({documentation: body,
                         documentationLoading: false});
        })
        .catch((error) => {
          this.setState({documentation: error.message,
                         documentationLoading: false});
        });
    } else {
      this.setState({
        displaySidebar: !this.state.displaySidebar
      });
    }
  }
  render() {
    let mainStyle = {
      width: this.state.displaySidebar ? '70%' : '100%'
    };
    let sidebarStyle = {
      width: '30%',
      visibility: this.state.displaySidebar ? 'visible' : 'hidden'
    };

    let resultContent;
    if (this.state.resultLoading) {
      resultContent = 'Loading...';
    } else {
      resultContent = this.state.result || '';
    }

    let docsContent;
    if (this.state.documentationLoading) {
      docsContent = 'Loading...';
    } else {
      docsContent = this.state.documentation || '';
    }

    return (
      <div>
        <div className="float-left" style={mainStyle}>
          <div>
            <div className="float-left">
              <button onClick={this.submitQuery.bind(this)}>run</button>
            </div>
            <div className="float-right">
              <button onClick={this.toggleSidebar.bind(this)}>docs</button>
            </div>
            <QueryComponent ref="query" onSubmit={this.submitQuery.bind(this)}/>
            <div className="clear-both"></div>
          </div>
          <ResultComponent content={resultContent}/>
        </div>
        <div className="float-right" style={sidebarStyle}>
          <DocsComponent content={docsContent}/>
        </div>
        <div className="clear-both"></div>
      </div>
    )
  }
}

ReactDOM.render(<Console/>, document.getElementById('container'));
