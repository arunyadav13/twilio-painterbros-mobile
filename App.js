import React from "react";
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';
import CallButton from "./frontend/CallModule/CallButton/CallButton";

class App extends React.Component {
  render() {
    return (
      
      <View style={styles.container}>
        <Text>Open up App.js to start working on your app!</Text>
        {/* <Icon name={'align-right'} /> */}
        <CallButton />
        <StatusBar style="auto" />
        
      </View>
    )
  }
}
export default App;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
