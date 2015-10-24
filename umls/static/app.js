
      var vocabApp = angular.module('vocabApp', ['ngProgress','chieffancypants.loadingBar','ngAnimate']);
      vocabApp.controller('VocabApiCtrl', function ($scope, $http,ngProgress){
        $scope.resourceNames = [{name: "concepts",id:"concepts" },{name: "codes" },{name: "concepts_bulk" }];
        $scope.host="";
        $scope.user="";
        $scope.token="";
        $scope.api_data ={
        value_sets:{},
        selectedApi:{},
        apis: []};
        $http.get('static/api-def.json').
        success(function(data, status, headers, config) {
         console.log("DATA",data[0].header[0].host);
            $scope.api_data.selectedApi = data[0].data[0];
            $scope.api_data.apis = data[0].data;
            $scope.api_data.value_sets = data[0].value_sets;
            $scope.host = data[0].header[0].host;
                    
        })
        .error(function(data, status, headers, config) {
        
        });
        // $.getJSON('api-def.json', function(data) {
        // $scope.api_data2 = data;
        //   console.log(this.api_data2);
        // });

        // $scope.selectedApi = "concepts";
        $scope.url = '';
        $scope.errors = {};

        $scope.compose_url = function(params) {
          console.log("params",params);
          url = this.api_data.selectedApi.resource;
          array = params;
          obj = {}
          //adding query paramatere parameters
          for (var i=0; i<array.length; i++){
            if(array[i].query_param == false){
              if(i==0)
                url= url+this.api_data.selectedApi.semantic_url;
              // console.log("nadeem",this.api_data.selectedApi.url);
             // url = this.api_data.selectedApi.resource; 
             // console.log(1,url);
             // url= url+this.api_data.selectedApi.url;
             console.log(2,url);
             url = url.replace(":"+array[i].name,array[i].value);
              console.log(3,url);
            }
            else{

               if (array[i].value != ''){
               
                obj[array[i].name] = array[i].value;
              }
            //   if (array[i].value != ''){
            //     if (url == '' ){  
            //       url = this.api_data.selectedApi.resource+"?";
            //       url = url + array[i].name+"="+array[i].value;
            //     }
            //     else{

            //     url = url + "&"+array[i].name+"="+array[i].value;
            //   }
            // }
            
          }

        }
            obj['user'] = this.user;
            obj['token'] = this.toekn;
           if(Object.keys(obj).length>0)
           url = url +"?"+ $.param(obj);
           console.log(Object.keys(obj).length);
          return url;
        }

        $scope.validate_params = function(params) {

            this.errors = {};
            for (var i=0; i<params.length; i++){
            if(params[i].optional == false && params[i].value == '' ){
              // this.errors.push(params[i].name+" required");
              this.errors[params[i].name] = "required";
              // console.log(params[i].name+" required");
            }
                           
          }
          if(angular.equals({}, this.errors))
            return false;
        return true;

        }

        
        $scope.get_data = function(params) {
          $("body").scrollTop(0);
          ngProgress.height('3px');
          // ngProgress.color('#469408');
        
          $('#ngProgress-container').css({ "background-color": 'white',"margin-top":"80px","z-index": "99999"});
          ngProgress.start();
         if(!this.validate_params(params)){
            url = this.compose_url(params);
            // console.log("URL",url+"?user="+this.user+"&token="+this.token);
            host = this.host;
            this.url = host+url;
            console.log(this.url);
            $http.get(host+url).
          success(function(data, status, headers, config) {
            $scope.concepts = data;
            $(document).ready(function() {
            $("#jjson").jJsonViewer(data,{expanded: false});
            });
            
            $scope.status = status;
            $scope.headers = headers;
            $scope.config = config;
            ngProgress.complete();
            $( ".res" ).removeClass( "alert alert-danger" );
            $('html,body').animate({
              scrollTop: $(".res").offset().top},
              'slow');
          })
          .error(function(data, status, headers, config) {
          // called asynchronously if an error occurs
          // or server returns response with an error status.
            // $scope.concepts = data;
            // $(document).ready(function() {
            // $("#jjson").jJsonViewer(data,{expanded: false});
            // });
            $scope.concepts = [];
            $(document).ready(function() {
            $("#jjson").jJsonViewer([],{expanded: false});
            });
            $scope.status = status;
            $scope.headers = headers;
            $scope.config = config;
            ngProgress.complete();
            // $( ".res" ).toggleClass( "alert-success" )
            $( ".res" ).addClass( "alert alert-danger" );
            $('html,body').animate({
              scrollTop: $(".res").offset().top},
              'slow');
          });
        
        }
        else{
             ngProgress.complete();
            $('html,body').animate({
              scrollTop: $(".params").offset().top},
              'slow');

        }
    }
        // $http.get('http://23.239.3.60/concepts?term=Chronic%20pain').
        // success(function(data, status, headers, config) {
        //   $scope.concepts = data;
        //   $scope.status = status;
        //   $scope.headers = headers;
        //   $scope.config = config;
        // })
        // .error(function(data, status, headers, config) {
        // // called asynchronously if an error occurs
        // // or server returns response with an error status.
        // });
      });
vocabApp.config(function($interpolateProvider) {
  $interpolateProvider.startSymbol('((');
  $interpolateProvider.endSymbol('))');
});
vocabApp.factory('timestampMarker', [function() {  
    var timestampMarker = {
        request: function(config) {
            config.requestTimestamp = new Date().getTime();
            return config;
        },
        response: function(response) {
            response.config.responseTimestamp = new Date().getTime();
            return response;
        }
    };
    return timestampMarker;
}]);
vocabApp.config(['$httpProvider', function($httpProvider) {  
    $httpProvider.interceptors.push('timestampMarker');
}]);