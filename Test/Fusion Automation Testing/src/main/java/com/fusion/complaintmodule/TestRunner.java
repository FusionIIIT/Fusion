package com.fusion.complaintmodule;


import cucumber.api.CucumberOptions;


@CucumberOptions(features="/src/main/resources/main.feature",glue="com.fusion.complaintmodule",plugin="html:target/test-report")
public class TestRunner{
	
}