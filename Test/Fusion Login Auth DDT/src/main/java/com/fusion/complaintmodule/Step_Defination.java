package com.fusion.complaintmodule;
import java.util.concurrent.TimeUnit;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.interactions.Actions;
import org.testng.Assert;

import cucumber.api.java.en.Given;
import cucumber.api.java.en.Then;
import cucumber.api.java.en.When;
public class Step_Defination {
	WebDriver driver;
	@Given("^User have opened the browser$")
	public void Open_the_browser() throws Throwable {
		System.setProperty("webdriver.chrome.driver", "C:\\Selenium\\driver\\chromedriver_win32\\chromedriver.exe");
		driver=new ChromeDriver();
	}

	@When("^User have opened Fusion website and verify the title$")
	public void Navigating_to_fusion_login() throws Throwable {
		driver.get("http://172.27.16.216/accounts/login/");
		String ActualTitle = driver.getTitle();
		String ExpectedTitle = "Fusion!";
		driver.manage().window().maximize();
		//Soft assert applied to verify title
		Assert.assertEquals(ActualTitle, ExpectedTitle);

	}
	
	@When("^User entered username as \"([^\"]*)\" and password as \"([^\"]*)\"$")
	public void Login(String arg1, String arg2) throws Throwable {
		
		 driver.manage().timeouts().implicitlyWait(3, TimeUnit.SECONDS);
		 driver.findElement(By.xpath("//*[@id=\"id_login\"]")).sendKeys(arg1);
		 driver.findElement(By.xpath("//*[@id=\"id_password\"]")).sendKeys(arg2);
		 driver.findElement(By.xpath("/html/body/div[1]/div[2]/form/div[4]/button")).click();
		
	}

	@Then("^Pressed Login Button$")
	public void login_button_should_exist() throws Throwable {
		String ActualTitle = driver.getTitle();
		String ExpectedTitle = "Fusion! Dashboard";
		Assert.assertEquals(ActualTitle, ExpectedTitle);
	    
	}
	@Then("^Dashboard Must appear and verify the dasboard Title$")
	public void Verify_Dashboard_Title() throws Throwable {
		String ActualTitle = driver.getTitle();
		String ExpectedTitle = "Fusion! Dashboard";
		Assert.assertEquals(ActualTitle, ExpectedTitle);
	    
	}
	@When("^click on complaint Module$")
	public void Verify_Complaint_Module() throws Throwable {
		driver.findElement(By.xpath("/html/body/div[2]/div[2]/div[4]/div/div/div/div/div/div/div[4]/div[2]/a/div/div[2]/span")).click();
		String ActualTitle = driver.getTitle();
		String ExpectedTitle = "Fusion! Complaint";
		Assert.assertEquals(ActualTitle, ExpectedTitle);
	    
	}
	@Then("^Fill the form and select the Electricity as complaint type and Location as Hall3\r\n" + 
			"$")
	public void Verify_Electricity_And_Hall3_Combination() throws Throwable {
		//Instantiate Action Class        
        Actions actions = new Actions(driver);
        //Retrieve WebElement 'Complaint Type' to perform mouse hover 
    	WebElement Complaint_Type = driver.findElement(By.xpath("/html/body/div[2]/div[2]/div[3]/div[1]/div[2]/div/form/div[2]/div[1]/div"));
    	//Mouse hover menuOption 'Complaint Type'
    	actions.moveToElement(Complaint_Type).perform();
    	//Now Select 'Electricity' from sub menu which has got displayed on mouse hover of 'Complaint Type'
    	WebElement subMenuOption = driver.findElement(By.xpath("/html/body/div[2]/div[2]/div[3]/div[1]/div[2]/div/form/div[2]/div[1]/div/div[2]/div[1]")); 
    	
    	subMenuOption.click();
    	
    	
    	WebElement Location = driver.findElement(By.xpath("/html/body/div[2]/div[2]/div[3]/div[1]/div[2]/div/form/div[2]/div[2]/div"));
    	//Mouse hover Location 
    	actions.moveToElement(Location).perform();
    	//Now Select 'Hall 3' from sub menu which has got displayed on mouse hover of 'Location'
    	WebElement subMenu_loc_Option = driver.findElement(By.xpath("/html/body/div[2]/div[2]/div[3]/div[1]/div[2]/div/form/div[2]/div[2]/div/div[2]/div[2]")); 
    	
    	subMenu_loc_Option.click();
    	
    	driver.findElement(By.xpath("/html/body/div[2]/div[2]/div[3]/div[1]/div[2]/div/form/div[3]/div/input")).sendKeys("D 304 Washroom");
		driver.findElement(By.xpath("/html/body/div[2]/div[2]/div[3]/div[1]/div[2]/div/form/div[4]/input")).sendKeys("Leakage in bathroom");
		driver.findElement(By.xpath("/html/body/div[2]/div[2]/div[3]/div[1]/div[2]/div/form/button")).click();
	}
	
	
}
