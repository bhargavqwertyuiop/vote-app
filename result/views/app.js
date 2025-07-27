var app = angular.module('catsvsdogs', []);
var socket = io.connect();

var bg1 = document.getElementById('background-stats-1');
var bg2 = document.getElementById('background-stats-2');

app.controller('statsCtrl', function($scope, $timeout){
  var animationDelay = 1500;
  
  // Initialize scope variables
  $scope.aPercent = 50;
  $scope.bPercent = 50;
  $scope.total = 0;
  $scope.a = 0;
  $scope.b = 0;
  $scope.connected = false;
  $scope.updating = false;
  $scope.lastUpdate = new Date();
  $scope.hostname = 'Unknown';

  // Connection status handlers
  socket.on('connect', function(){
    console.log('Connected to server');
    $scope.connected = true;
    $scope.$apply();
  });

  socket.on('disconnect', function(){
    console.log('Disconnected from server');
    $scope.connected = false;
    $scope.$apply();
  });

  socket.on('reconnect', function(){
    console.log('Reconnected to server');
    $scope.connected = true;
    $scope.$apply();
  });

  // Vote update handler
  socket.on('scores', function (json) {
    console.log('Received scores:', json);
    
    $scope.updating = true;
    
    // Update vote counts
    var data = JSON.parse(json);
    var a = parseInt(data.a || 0);
    var b = parseInt(data.b || 0);
    var total = a + b;
    
    // Calculate percentages
    var aPercent = total > 0 ? Math.round((a / total) * 100) : 50;
    var bPercent = total > 0 ? Math.round((b / total) * 100) : 50;
    
    // Ensure percentages add up to 100%
    if (total > 0 && aPercent + bPercent !== 100) {
      if (a > b) {
        aPercent = 100 - bPercent;
      } else {
        bPercent = 100 - aPercent;
      }
    }
    
    // Update scope with animation delay
    $timeout(function() {
      $scope.a = a;
      $scope.b = b;
      $scope.total = total;
      $scope.aPercent = aPercent;
      $scope.bPercent = bPercent;
      $scope.lastUpdate = new Date();
      $scope.updating = false;
      
      // Update hostname if provided
      if (data.hostname) {
        $scope.hostname = data.hostname;
      }
      
      console.log('Updated stats:', {
        a: $scope.a,
        b: $scope.b,
        total: $scope.total,
        aPercent: $scope.aPercent,
        bPercent: $scope.bPercent
      });
    }, animationDelay);
  });

  // Error handling
  socket.on('error', function(error) {
    console.error('Socket error:', error);
    $scope.connected = false;
    $scope.$apply();
  });

  // Initialize with body fade-in effect
  $timeout(function() {
    document.body.style.opacity = 1;
  }, 100);

  // Periodic connection check
  var connectionCheckInterval = setInterval(function() {
    if (!$scope.connected) {
      console.log('Attempting to reconnect...');
      socket.connect();
    }
  }, 5000);

  // Cleanup on scope destroy
  $scope.$on('$destroy', function() {
    if (connectionCheckInterval) {
      clearInterval(connectionCheckInterval);
    }
    socket.disconnect();
  });

  // Add some debug info
  console.log('Stats controller initialized');
  console.log('Socket connected:', socket.connected);
});

function getPercentages(a, b) {
  var result = {};

  if (a + b > 0) {
    result.a = Math.round(a / (a + b) * 100);
    result.b = 100 - result.a;
  } else {
    result.a = result.b = 50;
  }

  return result;
}